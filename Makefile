all: help

help:
	-@echo "serve     run a server on localhost"
	-@echo "deploy    upload to the cloud"

serve:
	$(GAE_DIR)/dev_appserver.py --enable_sendmail -a 0.0.0.0 .

deploy:
	$(GAE_DIR)/appcfg.py -e "$(MAIL)" update .
