# get all targets from subdirectory
SUBDIR := k8s/subcharts
TARGETS := $(shell make -C $(SUBDIR) -rpn | sed -n -e "/^$$/ { n ; /^[^ .\#%][^ ]\*:/ { s/:.\*$$// ; p ; } ; }" )

all:
	make -C $(SUBDIR) $@
	(cd k8s && helm upgrade backend app/ -i)

# pass all targets to subdirectory
%:
	make -C $(SUBDIR) $@