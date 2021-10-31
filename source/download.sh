wget https://github.com/hfg-gmuend/openmoji/releases/latest/download/openmoji-72x72-color.zip -P ./plugin_data/ReactionsPlugin
mkdir ./plugin_data/ReactionsPlugin/emoji
unzip ./plugin_data/ReactionsPlugin/openmoji-72x72-color.zip -d ./plugin_data/ReactionsPlugin/emoji
rm ./plugin_data/ReactionsPlugin/openmoji-72x72-color.zip