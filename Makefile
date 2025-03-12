.DEFAULT_GOAL := help

# https://www.gnu.org/software/make/manual/html_node/Force-Targets.html#Force-Targets
.FORCE:

# List of architectures to be tested
ARCHES = x86_64 aarch64

generate-zuul-config: .FORCE  ## Generate zuul configuration from list of tmt plans
	jinja2 -D arches="$(ARCHES)" -D plans="$$(tmt plan ls | tr '\n' ' ')" .zuul.yaml.j2 -o .zuul.yaml

# See https://www.thapaliya.com/en/writings/well-documented-makefiles/ for details.
reverse = $(if $(1),$(call reverse,$(wordlist 2,$(words $(1)),$(1)))) $(firstword $(1))

help: .FORCE  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "$(info $(PRELUDE))"} /^[a-zA-Z_/-]+:.*?##/ { printf "  \033[36m%-35s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(call reverse, $(MAKEFILE_LIST))
