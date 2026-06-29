from shieldlab.io.runner import _wsl_path


def test_wsl_path_translates_windows_drive_path_to_mnt_mount():
    distro, translated = _wsl_path(r"D:\projects\ShieldLabG4\build\generated.mac")

    assert distro is None
    assert translated == "/mnt/d/projects/ShieldLabG4/build/generated.mac"


def test_wsl_path_preserves_unc_style_wsl_path():
    distro, translated = _wsl_path(r"//wsl$/Ubuntu/mnt/d/projects/ShieldLabG4/build/generated.mac")

    assert distro == "Ubuntu"
    assert translated == "/mnt/d/projects/ShieldLabG4/build/generated.mac"