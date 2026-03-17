#!/usr/bin/env python3

# This Python script is only used to check 
# whether some of the required problems in the PA HAVE BEEN IMPLEMENTED. 
# And CANNOT be used to verify whether the problems are IMPLEMENTED CORRECTLY.

from __future__ import annotations

import re
import os
import subprocess
import contextlib
import sys
from pathlib import Path

ANSI_FG_BLACK       =   "\33[1;30m"
ANSI_FG_RED         =   "\33[1;31m"
ANSI_FG_GREEN       =   "\33[1;32m"
ANSI_FG_YELLOW      =   "\33[1;33m"
ANSI_FG_BLUE        =   "\33[1;34m"
ANSI_FG_MAGENTA     =   "\33[1;35m"
ANSI_FG_CYAN        =   "\33[1;36m"
ANSI_FG_WHITE       =   "\33[1;37m"
ANSI_BG_BLACK       =   "\33[1;40m"
ANSI_BG_RED         =   "\33[1;41m"
ANSI_BG_GREEN       =   "\33[1;42m"
ANSI_BG_YELLOW      =   "\33[1;43m"
ANSI_BG_BLUE        =   "\33[1;44m"
ANSI_BG_MAGENTA     =   "\33[1;45m"
ANSI_BG_CYAN        =   "\33[1;46m"
ANSI_BG_WHITE       =   "\33[1;47m"
ANSI_FG_CYAN_LIGHT  =   "\33[0;36m"
ANSI_NONE           =   "\33[0m"
ANSI_CLEAR_SCREEN   =   "\33[2J\33[H"

class NEMU:
    HOME: Path
    YSYX_HOME: Path
    TRACER_BRANCH = "tracer-ysyx"
    _config_file: Path
    _kconfig_file: Path
    _conf_bin: Path

    @staticmethod
    def setup(NEMU_HOME: Path):
        NEMU.HOME = NEMU_HOME
        NEMU.YSYX_HOME = NEMU.HOME.parent
        NEMU._config_file = NEMU.HOME / ".config"
        # Kconfig       := $(NEMU_HOME)/Kconfig
        NEMU._kconfig_file = NEMU.HOME / "Kconfig"
        # KCONFIG_PATH  := $(NEMU_HOME)/tools/kconfig
        # CONF          := $(KCONFIG_PATH)/build/conf
        NEMU._conf_bin = NEMU.HOME / "tools" / "kconfig" / "build" / "conf"

    @staticmethod
    def run(cmd_list, timeout=10):
        try:
            process = subprocess.Popen(
                ["make", "run"],
                cwd=NEMU.HOME,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            for cmd in cmd_list:
                process.stdin.write(cmd)
                process.stdin.write("\n")
                process.stdin.flush()

            output, _ = process.communicate("q\n", timeout=timeout)
            output = output.split("(nemu)")
            return process.returncode, output[1:]
        except Exception:
            return None, None

    @staticmethod
    def create_tracer_record(message: str) -> str | None:
        env = os.environ.copy()
        env["NEMU_HOME"] = str(NEMU.HOME)

        try:
            subprocess.run(
                ["make", ".git_commit", f"MSG={message}"],
                cwd=NEMU.YSYX_HOME,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
        except Exception:
            return None

        try:
            commit = subprocess.run(
                ["git", "rev-parse", NEMU.TRACER_BRANCH],
                cwd=NEMU.YSYX_HOME,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
        except Exception:
            return None

        NEMU.TRACER_COMMIT_ID = commit.stdout.strip()

    @staticmethod
    def get_commit_info(commit_id: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "show", "-s", "--format=fuller", commit_id],
                cwd=NEMU.YSYX_HOME,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
        except Exception:
            return None

        return result.stdout

    @staticmethod
    def _syncconfig():
        subprocess.run(
            [str(NEMU._conf_bin), "--syncconfig", str(NEMU._kconfig_file)],
            cwd=NEMU.HOME,
            check=True,
        )

    @staticmethod
    def _patch_config_text(text: str, changes: dict[str, object]) -> str:
        for key, value in changes.items():
            if not key.startswith("CONFIG_"):
                raise ValueError(f"{key} must start with CONFIG_")

            if isinstance(value, bool):
                text = NEMU._set_bool(text, key, value)
            elif isinstance(value, int):
                text = NEMU._set_value(text, key, str(value))
            elif isinstance(value, str):
                text = NEMU._set_value(text, key, f"\"{value}\"")
            else:
                raise TypeError(f"unsupported value type for {key}: {type(value)}")

        return text

    @staticmethod
    def _set_bool(text: str, key: str, enabled: bool) -> str:
        yes_pat = re.compile(rf"^{re.escape(key)}=y$", re.M)
        no_pat = re.compile(rf"^# {re.escape(key)} is not set$", re.M)

        if enabled:
            if yes_pat.search(text):
                return text
            if no_pat.search(text):
                return no_pat.sub(f"{key}=y", text, count=1)
            return text.rstrip("\n") + f"\n{key}=y\n"

        if no_pat.search(text):
            return text
        if yes_pat.search(text):
            return yes_pat.sub(f"# {key} is not set", text, count=1)
        return text.rstrip("\n") + f"\n# {key} is not set\n"

    @staticmethod
    def _set_value(text: str, key: str, value: str) -> str:
        set_pat = re.compile(rf"^{re.escape(key)}=.*$", re.M)
        unset_pat = re.compile(rf"^# {re.escape(key)} is not set$", re.M)

        if set_pat.search(text):
            return set_pat.sub(f"{key}={value}", text, count=1)
        if unset_pat.search(text):
            return unset_pat.sub(f"{key}={value}", text, count=1)
        return text.rstrip("\n") + f"\n{key}={value}\n"

    @staticmethod
    @contextlib.contextmanager
    def config(changes: dict[str, object]):
        if not NEMU._config_file.exists():
            raise RuntimeError(f"{NEMU._config_file} does not exist, run make menuconfig once first")

        original = NEMU._config_file.read_text()

        try:
            new_text = NEMU._patch_config_text(original, changes)
            NEMU._config_file.write_text(new_text)
            NEMU._syncconfig()

            yield NEMU
        finally:
            NEMU._config_file.write_text(original)
            NEMU._syncconfig()
    
    @staticmethod
    @contextlib.contextmanager
    def itrace_enabled():
        # config ITRACE
        #   depends on TRACE && TARGET_NATIVE_ELF && ENGINE_INTERPRETER
        #   bool "Enable instruction tracer"
        #   default y

        # config ITRACE_COND
        #   depends on ITRACE
        #   string "Only trace instructions when the condition is true"
        #   default "true"
        itrace_enabled_config = {
            "CONFIG_TRACE": True,
            "CONFIG_NATIVE_ELF": True,
            "CONFIG_ENGINE_INTERPRETER": True,
            "CONFIG_ITRACE": True,
            "CONFIG_ITRACE_COND": "true",
        }
        with NEMU.config(itrace_enabled_config):
            yield NEMU


def is_output_valid(output : str):
    # output 形如
    # info r 
    # xxx
    return (output is not None
        and len(output.splitlines()) > 1
        # 未知的指令或者操作符
        and "Unknown" not in output
        # Error(xxx)
        and ANSI_FG_RED not in output
        )


def check_env():
    nemu_home = os.environ.get("NEMU_HOME")
    if not nemu_home:
        return False

    if not os.path.isdir(nemu_home):
        return False
    NEMU.setup(Path(nemu_home))
    return True


def check_exit_gracefully():
    ret,_  = NEMU.run(["q"])
    if ret != 0:
        return False

    return True

def check_info_r():
    cmd = ["info r", 'q']
    ret, output = NEMU.run(cmd)
    if not is_output_valid(output[0]):
        return False

    return True

def check_watch_point():
    cmd = ["w 0", "info w", 'q']
    ret, output = NEMU.run(cmd)
    if not is_output_valid(output[1]):
        return False

    return True 

def check_cmd_x():
    cmd = ["x 10 0x80000000", 'q']
    ret, output = NEMU.run(cmd)
    if not is_output_valid(output[0]):
        return False
    return True

def check_extended_cmd_x():
    cmd = ["x 10 0x80000000 + (0 == 0)", 'q']
    ret, output = NEMU.run(cmd)
    if not is_output_valid(output[0]):
        return False
    return True

def check_cmd_si():
    cmd = ["si 1", 'q']
    try:
        with NEMU.itrace_enabled():
            ret, output = NEMU.run(cmd)
            if not is_output_valid(output[0]):
                return False
    except Exception:
        return False
    return True

def check_cmd_p():
    cmd = ["p 1 + 2 * 3", 'q']
    ret, output = NEMU.run(cmd)
    if not is_output_valid(output[0]):
        return False
    return True

def check_gen_expr():
    GEN_EXPR = NEMU.HOME / "tools" / "gen-expr" /"gen-expr.c"
    result = subprocess.run(["git", "log", "tracer-ysyx", "--oneline", GEN_EXPR], cwd=NEMU.HOME, stdout=subprocess.PIPE, text=True)
    if len(result.stdout.splitlines()) <= 1: # 必然有一行是仓库初始化, 至少还有一行是修改了 gen-expr.c 的记录
        return False
    return True

def info(message: str):
    print(f"{ANSI_FG_BLUE}{message}{ANSI_NONE}")

def prompt_student_info():
    info("所有测试均通过，请输入以下信息：")
    try:
        input("姓名: ")
        input("报名号: ")
        input("手机号: ")
    except EOFError:
        return False
    return True

def print_submission_commit(commit_id: str):
    commit_info = NEMU.get_commit_info(commit_id)
    if commit_info is None:
        print(f"{ANSI_FG_RED}failed to read tracer commit {commit_id}{ANSI_NONE}")
        return False

    print(commit_info, end="" if commit_info.endswith("\n") else "\n")
    info("请将以上测试通过信息以及提交记录截图提交到问卷中。")
    return True

def main():
    print(ANSI_CLEAR_SCREEN, end="")
    sys.stdout.flush()
    info("正在检查环境和功能实现，请稍候...")
    info("本工具仅检查部分功能是否实现，并不保证功能的正确性。")
    if not check_env():
        print(f"{ANSI_FG_RED}NEMU_HOME is not set or invalid{ANSI_NONE}")
        return 1

    NEMU.create_tracer_record("run pretest")
    if NEMU.TRACER_COMMIT_ID is None:
        print(f"{ANSI_FG_RED}failed to create tracer record for run pretest{ANSI_NONE}")
        return 1

    check_list = [
        check_env,
        check_exit_gracefully, 
        check_info_r, 
        check_watch_point, 
        check_cmd_x, 
        check_extended_cmd_x, 
        check_cmd_si, 
        check_cmd_p, 
        check_gen_expr
    ]
    max_name_length = max(len(check.__name__) for check in check_list)
    all_passed = True
    for check in check_list:
        success = check()
        if success:
            print(f"{check.__name__:<{max_name_length}}: {ANSI_FG_GREEN}PASS{ANSI_NONE}")
        else:
            print(f"{check.__name__:<{max_name_length}}: {ANSI_FG_RED  }FAIL{ANSI_NONE}")
            all_passed = False

    if not all_passed:
        return 1

    if not prompt_student_info():
        print(f"{ANSI_FG_RED}failed to read student information from terminal{ANSI_NONE}")
        return 1

    if not print_submission_commit(NEMU.TRACER_COMMIT_ID):
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
