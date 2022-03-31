#
# def sort_by_commit_date(lst):
#     return sorted(lst, key=lambda c: c.committed_date, reverse=False)
#
#
# def bfs_find_tag(head, tags):
#     q = deque()
#
#     def add_parents(c):
#         q.extend(sorted(c.parents, key=lambda c: c.committed_date))
#
#     add_parents(head)
#     visited = {head}
#     while q:
#         c = q.pop()
#         if c in visited:
#             continue
#         if c.hexsha in tags:
#             break
#         add_parents(c)
#         visited.add(c)
#     return sort_by_commit_date(visited)
#
#
# def list_branch_only_commits(repo, branch, reference):
#     ref_commits = set(repo.iter_commits(rev=reference))
#     branch_commits = [c for c in repo.iter_commits(rev=branch) if c not in ref_commits]
#     return sorted(branch_commits, key=lambda c: c.committed_date, reverse=False)
#
#
# def format_commit_message(msg):
#     lines = [line for line in (l.strip() for l in msg.splitlines()) if line]
#     if not lines:
#         return None
#     if len(lines) == 1:
#         return "* %s" % lines[0]
#     formatted = ["* %s" % lines[0]]
#     entry = None
#     for i in range(1, len(lines)):
#         l = lines[i]
#         if (
#             not entry
#             or l.startswith("*")
#             or len(l) < 2
#             or l[0].isupper()
#             and l[1].islower()
#         ):
#             if entry:
#                 formatted[-1] = " ".join(entry)
#             entry = ["    * %s" % l.lstrip("* ")]
#             formatted.append(entry)
#         else:
#             entry.append(l)
#     if entry:
#         formatted[-1] = " ".join(entry)
#     return "\n".join(formatted)
#
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Creates a KSP mod distribution " "and changelog file"
#     )
#     parser.add_argument(
#         "-d",
#         "--dir",
#         metavar="path",
#         type=str,
#         default=".",
#         help="Path to the root directory of the mod.",
#     )
#     parser.add_argument(
#         "-s",
#         "--source",
#         metavar="path",
#         type=str,
#         default="",
#         help="Relative path to the source directory.",
#     )
#     parser.add_argument(
#         "-e",
#         "--exclude",
#         metavar="paths",
#         type=str,
#         nargs="*",
#         default=[],
#         help="Files that should be excluded from the distribution. "
#         "Wildcards are supported.",
#     )
#     parser.add_argument(
#         "-i",
#         "--include",
#         metavar="paths",
#         type=str,
#         nargs="*",
#         default=[],
#         help="Paths that should be included into the distribution. "
#         "Exclude patterns are also applied here.",
#     )
#     parser.add_argument(
#         "-o",
#         "--output-dir",
#         metavar="path",
#         type=str,
#         default="",
#         help="Path to the root directory of the mod.",
#     )
#     parser.add_argument(
#         "--dll",
#         metavar="filename.dll",
#         type=str,
#         default="",
#         help="Name of the dll to search for to get the actual mod version.",
#     )
#     args = parser.parse_args()
#     # go to the root dir
#     root = args.dir
#     if not os.path.isdir(root):
#         print("No such directory:", root)
#         sys.exit(1)
#     os.chdir(root)
#     # use source and exclude
#     if args.source:
#         sources = [args.source]
#     if args.exclude:
#         exclude += args.exclude
#     # check if it is indeed the mod directory
#     if not os.path.exists("./GameData"):
#         print("No %s/GameData directory." % root)
#         sys.exit(1)
#     # check repository
#     repo = Repo(".")
#     if repo.bare:
#         print("Git repository is empty")
#         sys.exit(2)
#     # get mod name and current version
#     modname, version = None, None
#     wd = os.path.abspath(os.curdir)
#     for src in sources:
#         modname, version = parse_assembly_info(join(wd, src, assembly_info))
#         if modname and version:
#             break
#         modname, version = parse_assembly_info(
#             join(wd, src, "Properties", assembly_info)
#         )
#         if modname and version:
#             break
#     if not modname or not version:
#         print("Unable to determine mod name and version")
#         sys.exit(3)
#     # if version is dynamic, use exiftool to get the actual version
#     if "*" in version:
#         if args.dll:
#             dll = args.dll
#         else:
#             dll = modname + ".dll"
#         new_version = None
#         if dll[0] in "/.":
#             new_version = get_version_from_dll(dll)
#         else:
#             found = False
#             for dirname, dirs, files in os.walk("./GameData"):
#                 for f in files:
#                     if f == dll:
#                         found = True
#                         new_version = get_version_from_dll(os.path.join(dirname, f))
#                         break
#                 if found:
#                     break
#         if new_version is not None:
#             version = new_version
#     current = "%s-%s" % (modname, version)
#     # make distribution package
#     releases = args.output_dir or "Releases"
#     try:
#         os.mkdir(releases)
#     except:
#         pass
#     release = join(releases, current + ".zip")
#     print("Making release: %s\n" % release)
#     with zipfile.ZipFile(release, "w", zipfile.ZIP_DEFLATED) as zipf:
#         zip_dir(zipf, "GameData", exclude)
#         if args.include:
#             for incpath in args.include:
#                 zip_dir(zipf, incpath, exclude)
#     # get commit history
#     tags = dict(
#         (t.commit.hexsha, t.name)
#         for t in repo.tags
#         if t.name.startswith("v") and t.commit.hexsha != repo.head.commit.hexsha
#     )
#     branch = repo.iter_commits(rev=repo.head)
#     commits = []
#     for c in branch:
#         if c.hexsha in tags:
#             break
#         commits.append(c)
#     changelog = [format_commit_message(c.message) for c in sort_by_commit_date(commits)]
#     # write changelog
#     if changelog:
#         print()
#         print("\n".join(changelog))
#         chlog_file = join(releases, current + ".log")
#         with open(chlog_file, "w", encoding="utf8") as log:
#             log.write("\n".join(changelog).strip())
#         print("\nChangeLog:", chlog_file)
#     print("Done")
