from setuptools import setup, find_packages
setup(
    name = "docker_update_hosts",
    version = "0.1",
    requires=[
        'python-daemon',
        'docker-py',
    ],
    scripts = ["bin/docker_update_hosts"],
    packages = find_packages(),
)
