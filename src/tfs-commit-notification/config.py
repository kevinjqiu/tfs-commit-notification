import agent

TFS = r'"C:\Program Files\Microsoft Visual Studio 8\Common7\IDE\tf.exe"'
CLIENT = r'"C:\SRC\Client"'
SERVER = r'"C:\SRC\Server"'

agents = [agent.Agent(TFS, CLIENT), agent.Agent(TFS, SERVER),]

