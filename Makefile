build:
	docker build -f Dockerfile -t consul-driven-haproxy .

debug: build
	docker run -i -p 8082:80 -e CONDRI_HAPROXY_CONSUL=137.129.47.64:80 -e CONDRI_HAPROXY_SERVICE_NAME=synopsis_frontend_2015_6-8080 -t consul-driven-haproxy bash
