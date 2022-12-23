<b>Hi, this is music.bot </b><br>
<br>
<br>
First create dev account on Twitter. <br>
Add Twitter credentials to appval.py<br>
<b>Warning </b>Bot is using Twinnter API 1.1 <br>
<br>
<br>
Run bot by executing command: <br>
docker run -d -v local_folder_to_store_music:/music -v twitterdb:/sqldb --restart unless-stopped twitteryt

