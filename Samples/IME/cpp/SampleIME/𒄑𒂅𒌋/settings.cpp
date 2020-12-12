﻿#include "𒄑𒂅𒌋/settings.h"

#include <codecvt>
#include <filesystem>
#include <fstream>
#include <sstream>

#include <ShlObj_core.h>

#include "Globals.h"

namespace 𒄑𒂅𒌋 {

constexpr std::array<wchar_t, 256> GetLayout(
    std::array<wchar_t, 48> ansi_rows) {
  std::array<wchar_t, 256> virtual_key_code_to_character{};
  for (int i = 0; i < 47; ++i) {
    virtual_key_code_to_character[ANSIPrintableVirtualKeyCodes[i]] =
        ansi_rows[i];
  }
  return virtual_key_code_to_character;
}

std::filesystem::path ApplicationDirectory() {
  wchar_t dll_filename_data[MAX_PATH]{};
  auto const dll_filename_size =
      GetModuleFileName(Global::dllInstanceHandle,
                        dll_filename_data,
                        ARRAYSIZE(dll_filename_data));
  std::wstring_view dll_filename(dll_filename_data, dll_filename_size);
  return std::filesystem::path(dll_filename).parent_path().parent_path();
}

std::filesystem::path UserAppDataDirectory() {
  static std::wstring_view const appdata = [] {
    wchar_t* allocated = nullptr;
    SHGetKnownFolderPath(FOLDERID_RoamingAppData,
                         KF_FLAG_DEFAULT,
                         /*hToken=*/nullptr,
                         &allocated);
    return allocated;
  }();
  auto path = std::filesystem::path(appdata) / "mockingbirdnest" / "Xsux IME";
  if (!std::filesystem::exists(path)) {
    std::filesystem::create_directories(path);
  }
  return path;
}

std::filesystem::path AppDataFile(std::string_view name) {
  std::filesystem::path path = UserAppDataDirectory() / name;
  if (!std::filesystem::exists(path)) {
    std::filesystem::copy_file(ApplicationDirectory() / name, path);
  }
  return path;
}

class UnicodeFile {
 public:
  explicit UnicodeFile(std::filesystem::path path) {
    _wfopen_s(&file_, path.c_str(), L"r, ccs=UTF-8");
  }

  ~UnicodeFile() {
    if (file_ != nullptr) {
      std::fclose(file_);
    }
  }

  wchar_t get() {
    wchar_t c = EOF;
    if (file_ != nullptr) {
      c = std::fgetwc(file_);
    }
    return c == EOF ? u'\uFFFD' : c;
  }

  bool good() {
    return file_ != nullptr && !std::feof(file_);
  }

 private:
  std::FILE* file_ = nullptr;
};

UnicodeFile OpenUserLayoutFile() {
  return UnicodeFile(AppDataFile("layout.txt"));
}

UnicodeFile OpenUserFontsFile() {
  return UnicodeFile(AppDataFile("fonts.txt"));
}

std::wstring GetUserLatinFont() {
  UnicodeFile file = OpenUserFontsFile();
  for (std::wstring line; file.good(); line.clear()) {
    for (wchar_t c = file.get(); file.good(); c = file.get()) {
      if (c == L'\r' || c == L'\n') {
        break;
      }
      line.push_back(c);
    }
    if (line.starts_with(L"Latn:")) {
      return line.substr(5);
    }
  }
  return L"Segoe UI";
}

std::wstring GetUserCuneiformFont() {
  UnicodeFile file = OpenUserFontsFile();
  for (std::wstring line; file.good(); line.clear()) {
    for (wchar_t c = file.get(); file.good(); c = file.get()) {
      if (c == L'\r' || c == L'\n') {
        break;
      }
      line.push_back(c);
    }
    if (line.starts_with(L"Xsux:")) {
      return line.substr(5);
    }
  }
  return L"Segoe UI Historic";
}

std::array<wchar_t, 48> GetLayoutConfiguration() {
  UnicodeFile file = OpenUserLayoutFile();
  std::array<wchar_t, 48> result{
      L"EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"};
  for (int i = 0; i < 47;) {
    wchar_t const c = file.get();
    if (c == L'\r' || c == L'\n' || c == ' ') {
      continue;
    }
    result[i++] = c;
  }
  return result;
}

wchar_t LatinLayout::GetCharacter(const std::uint8_t virtual_key_code) {
  static auto layout = GetLayout(GetLayoutConfiguration());
  return layout[virtual_key_code];
}

}  // namespace 𒄑𒂅𒌋
