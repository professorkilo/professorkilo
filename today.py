if __name__ == '__main__':
    """
    Stats generator for GitHub user 'professorkilo', based on Andrew Grant (Andrew6rant)'s script.
    """
    print('Calculation times:')

    # Look up your user data
    user_data = user_getter(USER_NAME)
    user_time = 0.0
    OWNER_ID, acc_date = user_data
    formatter('account data', user_time)

    # No age/birthday
    age_data = ''
    age_time = 0.0

    # LOC and other stats
    total_loc = loc_query(['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 7)
    loc_time = 0.0
    if total_loc[-1]:
        formatter('LOC (cached)', loc_time)
    else:
        formatter('LOC (no cache)', loc_time)

    commit_data = commit_counter(7)
    commit_time = 0.0

    star_data = graph_repos_stars('stars', ['OWNER'])
    star_time = 0.0

    repo_data = graph_repos_stars('repos', ['OWNER'])
    repo_time = 0.0

    contrib_data = graph_repos_stars('repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])
    contrib_time = 0.0

    follower_data = follower_getter(USER_NAME)
    follower_time = 0.0

    # Remove Andrew-specific deleted-repo archive logic
    # (no repository_archive.txt / special handling for a different user)
    # if OWNER_ID == {'id': 'MDQ6VXNlcjU3MzMxMTM0'}:
    #     archived_data = add_archive()
    #     for index in range(len(total_loc) - 1):
    #         total_loc[index] += archived_data[index]
    #     contrib_data += archived_data[-1]
    #     commit_data += int(archived_data[-2])
 
    # Format added, deleted, and total LOC
    for index in range(len(total_loc) - 1):
        total_loc[index] = '{:,}'.format(total_loc[index])

    svg_overwrite(
        'dark_mode.svg',
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:-1],
    )
    svg_overwrite(
        'light_mode.svg',
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:-1],
    )

    print(
        '\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F',
        '{:<21}'.format('Total function time:'),
        '{:>11}'.format('%.4f' % (
            user_time
            + age_time
            + loc_time
            + commit_time
            + star_time
            + repo_time
            + contrib_time
        )),
        ' s \033[E\033[E\033[E\033[E\033[E\033[E\033[E\033[E',
        sep='',
    )

    print('Total GitHub GraphQL API calls:', '{:>3}'.format(sum(QUERY_COUNT.values())))
    for funct_name, count in QUERY_COUNT.items():
        print('{:<28}'.format(' ' + funct_name + ':'), '{:>6}'.format(count))
