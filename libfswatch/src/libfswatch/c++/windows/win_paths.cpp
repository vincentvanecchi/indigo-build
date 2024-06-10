/*
 * Copyright (c) 2015 Enrico M. Crisostomo
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
#include "libfswatch/c++/windows/win_paths.hpp"
#include "libfswatch/c++/libfswatch_exception.hpp"

#include <locale>
#include <codecvt>

using namespace std;

namespace fsw
{
  namespace win_paths
  {
    
    wstring posix_to_win_w(string path)
    {
      wstring_convert<codecvt_utf8_utf16<wchar_t>> _UTF_Converter;
      wstring result = _UTF_Converter.from_bytes(path);
      for (wchar_t& c : result) {
        if (c == L'/') {
          c = L'\\';
        }
      }
      return result;
    }

    string win_w_to_posix(wstring path)
    {
      wstring_convert<codecvt_utf8_utf16<wchar_t>> _UTF_Converter;
      string result = _UTF_Converter.to_bytes(path);
      for (char& c : result) {
        if (c == '\\') {
          c = '/';
        }
      }
      return result;
    }
  }
}
