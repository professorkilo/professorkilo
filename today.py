import datetime
import hashlib
import os
import time

import requests
from dateutil import relativedelta
from lxml import etree

HEADERS = {"authorization": "token " + os.environ["ACCESS_TOKEN"]}
USER_NAME = os.environ["USER_NAME"]

QUERY_COUNT = {
    "user_getter": 0,
    "follower_getter": 0,
    "graph_repos_stars": 0,
    "recursive_loc": 0,
    "graph_commits": 0,
    "loc_query": 0,
}

os.makedirs("cache", exist_ok=True)


def daily_readme(birthday):
    """
    Returns the length of time since I was born
    e.g. 'XX years, XX months, XX days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return "{} {}, {} {}, {} {}{}".format(
        diff.years,
        "year" + format_plural(diff.years),
        diff.months,
        "month" + format_plural(diff.months),
        diff.days,
        "day" + format_plural(diff.days),
        " 🎂 " if (diff.months == 0 and diff.days == 0) else "",
    )


def format_plural(unit):
    """Returns 's' for plural units"""
    return "s" if unit != 1 else ""


def simple_request(func_name, query, variables):
    """Returns a request, raises Exception if response fails."""
    request = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS,
    )

    if request.status_code == 200:
        return request
    raise Exception(
        func_name,
        " has failed with a",
        request.status_code,
        request.text,
        QUERY_COUNT,
    )


def graph_commits(start_date, end_date):
    """Uses GitHub's GraphQL v4 API to return my total commit count"""
    query_count("graph_commits")
    query = """
    query($start_date: DateTime!, $end_date: DateTime!, $login: String!) {
        user(login: $login) {
            contributionsCollection(from: $start_date, to: $end_date) {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }
    """
    variables = {
        "start_date": start_date,
        "end_date": end_date,
        "login": USER_NAME,
    }
    request = simple_request(graph_commits.__name__, query, variables)
    return int(
        request.json()["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]["totalContributions"]
    )


def graph_repos_stars(count_type, owner_affiliation, cursor=None, add_loc=0, del_loc=0):
    """
    Uses GitHub's GraphQL v4 API to return my total
    repository, star, or lines of code count.
    """
    query_count("graph_repos_stars")
    query = """
    query ($owner_affiliation: [RepositoryAffiliation],
           $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor,
                        ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            stargazers {
                                totalCount
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
    """
    variables = {
        "owner_affiliation": owner_affiliation,
        "login": USER_NAME,
        "cursor": cursor,
    }

    request = simple_request(graph_repos_stars.__name__, query, variables)
    if request.status_code == 200:
        if count_type == "repos":
            return request.json()["data"]["user"]["repositories"]["totalCount"]
        elif count_type == "stars":
            return stars_counter(
                request.json()["data"]["user"]["repositories"]["edges"]
            )


def stars_counter(data):
    """Count total stars in repositories owned by me"""
    total_stars = 0
    for node in data:
        total_stars += node["node"]["stargazers"]["totalCount"]
    return total_stars


def svg_overwrite(
    filename,
    age_data,
    commit_data,
    star_data,
    repo_data,
    contrib_data,
    follower_data,
    loc_data,
):
    """Parse SVG files and update elements with stats"""
    tree = etree.parse(filename)
    root = tree.getroot()

    # Update text values
    find_and_replace(root, "age_data", age_data)
    find_and_replace(root, "commit_data", commit_data)
    find_and_replace(root, "star_data", star_data)
    find_and_replace(root, "repo_data", repo_data)
    find_and_replace(root, "contrib_data", contrib_data)
    find_and_replace(root, "follower_data", follower_data)
    find_and_replace(root, "loc_data", loc_data[2])
    find_and_replace(root, "loc_add", loc_data[0])
    find_and_replace(root, "loc_del", loc_data[1])

    tree.write(filename, encoding="utf-8", xml_declaration=True)


def find_and_replace(root, element_id, new_text):
    """Finds the element in the SVG and replaces its text"""
    if isinstance(new_text, int):
        new_text = f"{'{:,}'.format(new_text)}"
    new_text = str(new_text)

    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def commit_counter(comment_size):
    """
    Counts up my total commits from cache file.
    Returns 0 if cache doesn't exist yet.
    """
    total_commits = 0
    filename = "cache/" + hashlib.sha256(USER_NAME.encode("utf-8")).hexdigest() + ".txt"
    try:
        with open(filename, "r") as f:
            data = f.readlines()
    except FileNotFoundError:
        return 0
    data = data[comment_size:]
    for line in data:
        parts = line.split()
        if len(parts) >= 3:
            total_commits += int(parts[2])
    return total_commits


def user_getter(username):
    """Returns the account ID and creation time of the user"""
    query_count("user_getter")
    query = """
    query($login: String!){
        user(login: $login) {
            id
            createdAt
        }
    }
    """
    variables = {"login": username}
    request = simple_request(user_getter.__name__, query, variables)
    return {"id": request.json()["data"]["user"]["id"]}, request.json()["data"]["user"][
        "createdAt"
    ]


def follower_getter(username):
    """Returns the number of followers of the user"""
    query_count("follower_getter")
    query = """
    query($login: String!){
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }
    """
    request = simple_request(follower_getter.__name__, query, {"login": username})
    return int(request.json()["data"]["user"]["followers"]["totalCount"])


def query_count(funct_id):
    """Counts how many times the GitHub GraphQL API is called"""
    QUERY_COUNT[funct_id] += 1


def perf_counter(funct, *args):
    """
    Calculates the time it takes for a function to run
    Returns the function result and the time differential
    """
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


def formatter(query_type, difference, funct_return=False, whitespace=0):
    """Prints a formatted time differential"""
    print("{:<23}".format(" " + query_type + ":"), sep="", end="")

    if difference > 1:
        print("{:>12}".format("%.4f" % difference + " s "))
    else:
        print("{:>12}".format("%.4f" % (difference * 1000) + " ms"))

    if whitespace:
        return f"{'{:,}'.format(funct_return): <{whitespace}}"
    return funct_return


if __name__ == "__main__":
    """
    Credits: Andrew Grant (Andrew6rant), 2022-2025
    Modified for professorkilo
    """
    print("Calculation times:")
    user_data, user_time = perf_counter(user_getter, USER_NAME)
    OWNER_ID, acc_date = user_data
    formatter("account data", user_time)
    age_data, age_time = perf_counter(daily_readme, datetime.datetime(1886, 5, 8))
    formatter("age calculation", age_time)

    # DISABLED: LOC counting causes timeouts
    total_loc = ["0", "0", "0", True]
    loc_time = 0.0
    formatter("LOC (disabled)", loc_time)

    commit_data, commit_time = perf_counter(commit_counter, 7)
    formatter("commits", commit_time)
    star_data, star_time = perf_counter(graph_repos_stars, "stars", ["OWNER"])
    formatter("stars", star_time)
    repo_data, repo_time = perf_counter(graph_repos_stars, "repos", ["OWNER"])
    formatter("repositories", repo_time)
    contrib_data, contrib_time = perf_counter(
        graph_repos_stars,
        "repos",
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"],
    )
    formatter("contributed repos", contrib_time)
    follower_data, follower_time = perf_counter(follower_getter, USER_NAME)
    formatter("followers", follower_time)

    svg_overwrite(
        "dark_mode.svg",
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc,
    )

    svg_overwrite(
        "light_mode.svg",
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc,
    )

    total_time = (
        user_time
        + age_time
        + loc_time
        + commit_time
        + star_time
        + repo_time
        + contrib_time
        + follower_time
    )
    print(
        "\033[F" * 8,
        "{:<21}".format("Total function time:"),
        "{:>11}".format("%.4f" % total_time),
        " s ",
        "\033[E" * 8,
        sep="",
    )

    print(
        "Total GitHub GraphQL API calls:",
        "{:>3}".format(sum(QUERY_COUNT.values())),
    )
    for funct_name, count in QUERY_COUNT.items():
        print(
            "{:<28}".format(" " + funct_name + ":"),
            "{:>6}".format(count),
        )
