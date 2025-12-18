if __name__ == '__main__':
    """
    Stats generator for GitHub user 'professorkilo', based on Andrew Grant (Andrew6rant)'s script.
    """
    print('Calculation times:')

    # Look up your user data
    user_data, user_time = perf_counter(user_getter, professorkilo)
    OWNER_ID, acc_date = user_data
    formatter('account data', user_time)

    # No age/birthday: just set a placeholder that will never be shown if your SVGs omit it
    #age_data = ''
    #age_time = 0.0

    # LOC and other stats
    total_loc, loc_time = perf_counter(
        loc_query,
        ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'],
        7
    )
    if total_loc[-1]:
        formatter('LOC (cached)', loc_time)
    else:
        formatter('LOC (no cache)', loc_time)

    commit_data, commit_time = perf_counter(commit_counter, 7)
    star_data, star_time = perf_counter(graph_repos_stars, 'stars', ['OWNER'])
    repo_data, repo_time = perf_counter(graph_repos_stars, 'repos', ['OWNER'])
    contrib_data, contrib_time = perf_counter(
        graph_repos_stars,
        'repos',
        ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER']
    )
    follower_data, follower_time = perf_counter(follower_getter, professorkilo)

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

    # Overwrite SVGs with your stats; if your SVGs have no age text, age_data will simply be unused
    svg_overwrite(
        'dark_mode.svg',
        #age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:-1],
    )
    svg_overwrite(
        'light_mode.svg',
        #age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:-1],
    )

    # Print total function time
    print(
        '\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F',
        '{:<21}'.format('Total function time:'),
        '{:>11}'.format('%.4f' % (
            user_time
            #+ age_time
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
