FROM thefab/centos-opinionated:centos6
MAINTAINER Fabien MARTY <fabien.marty@gmail.com>

# Add runtime dependencies
ADD root/build/add_runtime_dependencies.sh /build/add_runtime_dependencies.sh
RUN /build/add_runtime_dependencies.sh && \
    rm -f /etc/haproxy/haproxy.cfg

# Add build dependencies
#ADD root/build/add_common_buildtime_dependencies.sh /build/add_common_buildtime_dependencies.sh
#RUN /build/add_common_buildtime_dependencies.sh

# Add consul and consul-cli binaries
ADD root/build/add_consul_binary.sh /build/add_consul_binary.sh
ADD root/build/add_consul_cli.sh /build/add_consul_cli.sh
RUN /build/add_consul_binary.sh && \
    /build/add_consul_cli.sh

# Remove build dependencies
#ADD root/build/remove_buildtime_dependencies.sh /build/remove_buildtime_dependencies.sh
#RUN /build/remove_buildtime_dependencies.sh

# Add custom other files
COPY root /

ENV CONDRI_HAPROXY_SYSLOG_IP=127.0.0.1 \
    CONDRI_HAPROXY_SYSLOG_FACILITY=local2 \
    CONDRI_HAPROXY_MAXCONN=4000 \
    CONDRI_HAPROXY_FRONTEND_PORT=80 \
    CONDRI_HAPROXY_BALANCE=roundrobin \
    CONDRI_HAPROXY_FORWARDFOR="" \
    CONDRI_HAPROXY_TIMEOUT_HTTP_REQUEST=10s \
    CONDRI_HAPROXY_TIMEOUT_QUEUE=300s \
    CONDRI_HAPROXY_TIMEOUT_CONNECT=10s \
    CONDRI_HAPROXY_TIMEOUT_CLIENT=300s \
    CONDRI_HAPROXY_TIMEOUT_SERVER=300s \
    CONDRI_HAPROXY_TIMEOUT_HTTP_KEEP_ALIVE=10s \
    CONDRI_HAPROXY_TIMEOUT_CHECK=10s \
    CONDRI_HAPROXY_HTTP_CHECK=1 \
    CONDRI_HAPROXY_HTTP_CHECK_URL=/check \
    CONDRI_HAPROXY_SERVICE_NAME=TO_SET \
    CONDRI_HAPROXY_CONSUL=localhost:8085