# landevlist is a simple program that displays the MAC and IPv4 addresses of
# all devices connected in a LAN. It is licensed under the MIT License, copy of
# which is given below.
#
#
# MIT License
#
# Copyright (c) 2025-Present Arijit Kumar Das <arijitkdgit.official@gmail.com>.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from typing import *
import subprocess
import sys
import re
import multiprocessing
import shutil

MULTIPROC_PCOUNT = 5
NPLUS = 43


def show_help() -> None:
        print("Usage: landevlist")
        print("Lists devices connected to the local network (LAN) with their MAC and IPv4 addresses.\n")
        print("Output is formatted in a tabular structure for readability.")
        print("Only devices with an active connection will be displayed.\n")
        print("Copyright (c) 2025-Present Arijit Kumar Das <arijitkdgit.official@gmail.com> under MIT License.\n")


def show_missing_dependency() -> None:
        print("landevlist: A required program was not found on your system.")
        print("Required programs are: ip, ping")
        print("Make sure these packages are installed:")
        print("* iputils-ping (on Debian/Ubuntu), or")
        print("  iputils (on Arch/RHEL/Fedora)")
        print("* iproute2 (on Debian/Ubuntu/Arch), or")
        print("  iproute (on RHEL/Fedora)")
        print("Please note that package name may vary based on your distro repository upstream.")


def prereq_installed() -> bool:
        for req in ("ip", "ping"):
                if (not shutil.which(req)):
                        return False
        return True


def is_ip_reachable(ip: str) -> bool:
        proc = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
        stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, text = True)
        return (proc.returncode == 0)

                
def get_all_reachable_lan_devs() -> dict:
        proc = subprocess.run(["ip", "-4", "neigh", "show"],
        stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)

        procresultlines: List[str] = list(filter(len, proc.stdout.split("\n")))
        lan_dev: dict = {}
        
        if (procresultlines == []):
                return {}

        for line in procresultlines:
                mac_pattern = re.compile(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})")
                mac_match   = mac_pattern.search(line)
                if (mac_match is not None):
                        mac: str = mac_match.group(0)
                        ip: str  = line.split()[0]
                        lan_dev[mac] = ip

        with multiprocessing.Pool(processes = MULTIPROC_PCOUNT) as pool:
                all_macs: tuple = tuple(lan_dev.keys())
                all_ips: tuple = tuple(lan_dev.values())
                result = pool.map(is_ip_reachable, all_ips)
                for i in range(len(result)):
                        if (not result[i]): lan_dev.pop(all_macs[i])

        return lan_dev


def main():
        argc: int = len(sys.argv)
        
        if ((argc > 1) and (sys.argv[1] in
        ("help", "-help", "--help", "/help"))):
                show_help()
                sys.exit(0)

        if (not prereq_installed()):
                show_missing_dependency()
                sys.exit(1)
        
        reachable_devs: dict = get_all_reachable_lan_devs()
        
        if (reachable_devs == {}):
                print("No active devices on local network.")
                sys.exit(0)
        
        print("+" * NPLUS)
        print("|      Device MAC     |    IPv4 Address   |")
        print("+" * NPLUS)

        for dev in reachable_devs:
                print(f"|  {dev}  |  {reachable_devs[dev]}{' '*(17-len(reachable_devs[dev]))}|")
                print("+" * NPLUS)
                

if (__name__ == "__main__"):
        main()
