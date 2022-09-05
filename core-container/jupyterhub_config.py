from subprocess import check_call
import getpass
import json
import configparser
import os
from os import path
import pwd
import grp


c.Application.log_level = 'DEBUG'

# setup active directory login
config = configparser.ConfigParser()
config.read('/defaults.cfg')


if config.has_section("LocalGitHubOAuthenticator"):

    from oauthenticator.github import LocalGitHubOAuthenticator
    c.JupyterHub.authenticator_class = LocalGitHubOAuthenticator

    c.LocalGitHubOAuthenticator.oauth_callback_url = config[
        "LocalGitHubOAuthenticator"]["callback_url"]
    c.LocalGitHubOAuthenticator.client_id = config["LocalGitHubOAuthenticator"]["client_id"]
    c.LocalGitHubOAuthenticator.client_secret = config["LocalGitHubOAuthenticator"]["client_secret"]


if config.has_section("AzureAdOAuthenticator"):

    from oauthenticator.azuread import AzureAdOAuthenticator
    c.JupyterHub.authenticator_class = AzureAdOAuthenticator

    c.AzureAdOAuthenticator.tenant_id = config["AzureAdOAuthenticator"]["tenant_id"]
    c.AzureAdOAuthenticator.oauth_callback_url = config["AzureAdOAuthenticator"]["callback_url"]
    c.AzureAdOAuthenticator.client_id = config["AzureAdOAuthenticator"]["client_id"]
    c.AzureAdOAuthenticator.client_secret = config["AzureAdOAuthenticator"]["client_secret"]


c.ConfigurableHTTPProxy.auth_token = config["ConfigurableHTTPProxy"]["auth_token"]


# map users to af-hub user
c.Authenticator.username_map = {
    u: 'guest' for u in json.loads(config["Authenticator"]["users"])}
if config.getboolean("Authenticator", "own_home", fallback=False):
    c.Authenticator.username_map.update({u: u.replace(' ', '').replace(
        ',', '') for u in json.loads(config["Authenticator"]["admins"])})
else:
    admin_name = getpass.getuser()
    if admin_name != "admin":
        check_call(["ln", "-s", "/home/admin", f"/home/{admin_name}"])
    c.Authenticator.username_map.update(
        {u: admin_name for u in json.loads(config["Authenticator"]["admins"])})


# add sudospawner
if config.getboolean("Authenticator", "use_sudo", fallback=True):
    c.JupyterHub.spawner_class = 'sudospawner.SudoSpawner'


# setup ssl
c.Spawner.default_url = '/lab'
c.JupyterHub.ssl_key = '/key.pem'
c.JupyterHub.ssl_cert = '/cer.pem'

# keep all environ variables
for var in os.environ:
    c.Spawner.env_keep.append(var)

# c.LocalAuthenticator.create_system_users = True


def my_script_hook(spawner):
    username = spawner.user.name

    try:
        pwd.getpwnam(username)
        user_exists = True
    except KeyError:
        print(f'User {username} does not exist.')
        user_exists = False

    if not user_exists:

        try:
            check_call(["sudo", "useradd", "-m",
                       username, "-s", "/usr/bin/bash"])
            check_call(["sudo", "usermod", "-aG", "root", username])
            check_call(["sudo", "usermod", "-aG", "docker", username])
        except:
            check_call(["sudo", "mkdir", "-p", f"/home/{username}"])
            pass

        check_call(["sudo", "cp", "/home/admin/.bashrc",
                   f"/home/{username}/.bashrc"])
        check_call(["sudo", "cp", "/home/admin/.jupyterlab-proxy-gui-config.json",
                   f"/home/{username}/.jupyterlab-proxy-gui-config.json"])

        check_call(
            ["sudo", "chown", "-R", f"{username}:root", f"/home/{username}"])
        check_call(["sudo", "setfacl", "-Rm",
                   f"u:{username}:rwX,d:u:{username}:rwX", f"/home/admin/workflow"])

        check_call(["sudo", "ln", "-s", "/home/admin/workflow",
                   f"/home/{username}/workflow"])

    if path.exists('/home/admin/workflow/setup.sh'):
        check_call(['/home/admin/workflow/setup.sh', username])


# attach the hook function to the spawner
c.Spawner.pre_spawn_hook = my_script_hook
