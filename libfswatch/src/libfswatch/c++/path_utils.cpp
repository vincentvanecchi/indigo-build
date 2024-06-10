/*
 * Copyright (c) 2014-2021 Enrico M. Crisostomo
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 3, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <libfswatch/libfswatch_config.h>
#include "libfswatch/c++/path_utils.hpp"
#include "libfswatch/c/libfswatch_log.h"

#ifdef HAVE_WINDOWS
#include <windows.h>
#include "libfswatch/c++/windows/win_strings.hpp"
#include "libfswatch/c++/windows/win_paths.hpp"
#include "libfswatch/c++/windows/win_error_message.hpp"
#endif

#include "libfswatch/c++/libfswatch_exception.hpp"
#include <cstdlib>
#include <cstdio>
#include <cerrno>
#include <iostream>
#include <system_error>

using namespace std;

extern "C" {
  char* __cdecl realpath( const char * name, char * resolved );
}

namespace fsw
{
  vector<string> get_directory_children(const string& path)
  {
    vector<string> children;

#ifdef HAVE_WINDOWS
    wstring wpath = win_paths::posix_to_win_w(path);

    WIN32_FIND_DATAW find_file_data;
    HANDLE handle = FindFirstFileW(wpath.c_str(), &find_file_data);
    if (handle == INVALID_HANDLE_VALUE) {
      auto err = win_error_message::current();
      string errmsg = win_strings::wstring_to_string(err.get_message());
      errmsg.append(": ");
      errmsg.append(path);
      fsw_log_perror(errmsg.c_str());
      // throw libfsw_exception( win_strings::wstring_to_string(err.get_message()), err.get_error_code() );
    }

    do {
      // if (find_file_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
      // } else {
      // }
      children.push_back( win_paths::win_w_to_posix(find_file_data.cFileName ? find_file_data.cFileName : L"") );
    } while (FindNextFileW(handle, &find_file_data));

    FindClose(handle);
#else
    DIR *dir = opendir(path.c_str());

    if (!dir)
    {
      if (errno == EMFILE || errno == ENFILE)
      {
        perror("opendir");
      }
      else
      {
        fsw_log_perror("opendir");
      }

      return children;
    }

    while (struct dirent *ent = readdir(dir))
    {
      children.emplace_back(ent->d_name);
    }

    closedir(dir);
#endif
    return children;
  }

  bool read_link_path(const string& path, string& link_path)
  {
    link_path = fsw_realpath(path.c_str(), nullptr);

    return true;
  }

  std::string fsw_realpath(const char *path, char *resolved_path)
  {
    char *ret = realpath(path, resolved_path);

    if (ret == nullptr)
    {
      if (errno != ENOENT)
        throw std::system_error(errno, std::generic_category());

      return std::string(path);
    }

    std::string resolved(ret);

    if (resolved_path == nullptr) free(ret);

    return resolved;
  }

  bool stat_path(const string& path, struct stat& fd_stat)
  {
    if (stat(path.c_str(), &fd_stat) == 0)
      return true;

    fsw_logf_perror(_("Cannot stat %s"), path.c_str());
    return false;

  }

  bool lstat_path(const string& path, struct stat& fd_stat)
  {
  #ifndef HAVE_WINDOWS
    if (lstat(path.c_str(), &fd_stat) == 0)
      return true;
    fsw_logf_perror(_("Cannot lstat %s"), path.c_str());
    return false;
  #else
    return stat_path(path, fd_stat);
  #endif
  }
}
