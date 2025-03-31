docker run -d --restart=always --read-only \
  -p 8080:8080 \
  --cap-drop=SETPCAP --cap-drop=MKNOD --cap-drop=NET_BIND_SERVICE --cap-drop=SYS_CHROOT --cap-drop=SETFCAP --cap-drop=FSETID \
  --tmpfs /tmp \
  -v ./data/backend/test_case:/test_case:ro \
  -v ./data/judge_server/log:/log \
  -v ./data/judge_server/run:/judger \
  -e SERVICE_URL=http://oj-judge:8080 \
  -e BACKEND_URL=http://oj-backend:8000/api/judge_server_heartbeat/ \
  -e TOKEN=CHANGE_THIS \
  registry.cn-hongkong.aliyuncs.com/oj-image/judge:1.6.1


https://github.com/QingdaoU/JudgeServer/blob/master/client/Python/client.py

