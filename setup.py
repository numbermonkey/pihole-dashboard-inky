""" Tool Setup """
# !/usr/bin/env python3

import os
from shutil import copyfile
from setuptools import setup
from setuptools.command.install import install

PACKAGE_NAME = "pihole-dashboard-inky"
VERSION = "4.0.3"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


class PostInstallJob(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        print("Installing cronjob...")
        self_dir = os.path.dirname(os.path.realpath(__file__))
        cron_dir = os.path.join(self_dir, 'cron')
        copyfile(os.path.join(cron_dir, "pihole-dashboard-inky-cron"),
                 "/etc/cron.d/pihole-dashboard-inky-cron")
        print("Done.")


if __name__ == "__main__":
    setup(
        name=PACKAGE_NAME,
        version=VERSION,
        author="santoru fork numbermonkey",
        author_email="santoru@pm.me",
        description="Minimal dashboard for Pi-Hole that works with inky PHAT display",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/numbermonkey/pihole-dashboard-inky",
        packages=["pihole_dashboard_inky"],
        package_data={'pihole_dashboard_inky': ['font/*.ttf']},
        scripts=[
            "scripts/pihole-dashboard-inky-clean-screen",
            "scripts/pihole-dashboard-inky-draw"
        ],
        python_requires='>=3.3.5',
        install_requires=parse_requirements("requirements.txt"),
        cmdclass={
            'install': PostInstallJob,
        },
    )
