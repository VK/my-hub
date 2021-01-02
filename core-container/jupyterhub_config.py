import os
from os import path


c.Application.log_level = 'DEBUG'

#setup active directory login
import configparser
import json
config = configparser.ConfigParser()
config.read('/defaults.cfg')


if config.has_section("LocalGitHubOAuthenticator"):

    from oauthenticator.github import LocalGitHubOAuthenticator
    c.JupyterHub.authenticator_class = LocalGitHubOAuthenticator

    c.LocalGitHubOAuthenticator.oauth_callback_url = config["LocalGitHubOAuthenticator"]["callback_url"]
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


#map users to af-hub user
c.Authenticator.username_map  = { u: 'guest' for u in json.loads(config["Authenticator"]["users"])}
c.Authenticator.username_map.update({ u: 'admin' for u in json.loads(config["Authenticator"]["admins"])})

#add sudospawner
c.JupyterHub.spawner_class='sudospawner.SudoSpawner'

#setup ssl
c.Spawner.default_url = '/lab'
c.JupyterHub.ssl_key = '/key.pem'
c.JupyterHub.ssl_cert = '/cer.pem'

#keep all environ variables
for var in os.environ:
    c.Spawner.env_keep.append(var)



from subprocess import check_call
def my_script_hook(spawner):
    if path.exists('/home/admin/workflow/setup.sh'):
      check_call(['/home/admin/workflow/setup.sh'])

# attach the hook function to the spawner
c.Spawner.pre_spawn_hook = my_script_hook