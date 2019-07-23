FROM minio/minio


ENV MINIO_ACCESS_KEY=minioaccess
ENV MINIO_SECRET_KEY=miniosecret
ENV MINIO_HTTP_TRACE=/minio-data/requests.log

RUN mkdir /minio-data

VOLUME /minio-data

EXPOSE 9000

CMD ["server", "/minio-data"]
