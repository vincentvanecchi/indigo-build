/* #undef ENABLE_NLS */
/* #define LOCALEDIR         "/usr/local/share/locale" */
#define PACKAGE           "fswatch"
#define PACKAGE_NAME      "fswatch"
#define PACKAGE_VERSION   "1.17.1-msvc"
#define PACKAGE_STRING    "fswatch 1.17.1-msvc"
#define PACKAGE_BUGREPORT "vincent@newbject.com"
#define PACKAGE_TARNAME   "fswatch"
#define PACKAGE_URL       "https://github.com/vincentvanecchi/fswatch"
#define HAVE_GETOPT_LONG

/* #undef HAVE_FSEVENTS_FSEVENTSTREAMSETDISPATCHQUEUE */
/* #undef HAVE_PORT_H */
#define HAVE_STRUCT_STAT_ST_MTIME
/* #undef HAVE_STRUCT_STAT_ST_MTIMESPEC */
/* #undef HAVE_SYS_EVENT_H */
/* #undef HAVE_SYS_INOTIFY_H */
#define HAVE_UNORDERED_MAP
#define HAVE_UNORDERED_SET
#define HAVE_WINDOWS

/* #undef HAVE_MACOS_GE_10_5 */
/* #undef HAVE_MACOS_GE_10_7 */
/* #undef HAVE_MACOS_GE_10_9 */
/* #undef HAVE_MACOS_GE_10_10 */
/* #undef HAVE_MACOS_GE_10_13 */

#define _CRT_SECURE_NO_WARNINGS 1
#define WIN32_LEAN_AND_MEAN 1

// no idea where did it come from but aight
#ifndef _
#   define _(...) __VA_ARGS__
#endif
