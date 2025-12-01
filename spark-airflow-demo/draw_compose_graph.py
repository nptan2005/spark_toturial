import yaml
import os
from collections import defaultdict
from diagrams import Diagram, Cluster, Node # Node chung
from diagrams.onprem.monitoring import Prometheus, Grafana 
from diagrams.onprem.queue import Kafka, Zookeeper
from diagrams.onprem.database import PostgreSQL, Redis
from diagrams.onprem.datastore import Minio
from diagrams.onprem.security import Keycloak
from diagrams.generic.device import Server 
from diagrams.generic.network import Proxy 
from diagrams.generic.compute import Rack


# 1. Đọc cấu hình Docker Compose
compose_file_path = 'docker-compose.yml'
if not os.path.exists(compose_file_path):
    print(f"Lỗi: Không tìm thấy file {compose_file_path}.")
    exit()

try:
    with open(compose_file_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"Lỗi khi đọc hoặc phân tích file YAML: {e}")
    exit()

services = config.get('services', {})
output_filename = "cdp_architecture_diagram_clustered"

# 2. Định nghĩa Ánh xạ Tên Service và Nhóm (Cluster)
SERVICE_GROUPS = {
    'spark-master': 'Data Processing (Spark)',
    'spark-worker': 'Data Processing (Spark)',
    'jupyterlab': 'Development Environment',
    
    'postgres': 'Workflow Orchestration (Airflow)',
    'redis': 'Workflow Orchestration (Airflow)',
    'airflow-init': 'Workflow Orchestration (Airflow)',
    'airflow-webserver': 'Workflow Orchestration (Airflow)',
    'airflow-scheduler': 'Workflow Orchestration (Airflow)',
    'airflow-dag-processor': 'Workflow Orchestration (Airflow)',
    'flower': 'Workflow Orchestration (Airflow)',

    'minio': 'Storage (S3)',
    
    'zookeeper': 'Messaging (Kafka)',
    'kafka': 'Messaging (Kafka)',
    'kafka-client': 'Messaging (Kafka)',

    'keycloak': 'Security & Access',
    'spark-ui-proxy': 'Security & Access',

    'ranger': 'Data Governance',
    'postgres-marquez': 'Data Governance',
    'openlineage': 'Data Governance',
    'openmetadata': 'Data Governance',
    
    'prometheus': 'Observability Stack',
    'loki': 'Observability Stack',
    'promtail': 'Observability Stack',
    'grafana': 'Observability Stack',
    'cadvisor': 'Observability Stack',
    'nginx-prometheus-exporter': 'Observability Stack',
    'jaeger': 'Observability Stack',
    
    'access-host-proxy': 'Network/Proxy',
    'postgres-dwh': 'Data Warehouse (DWH)'
}

# Ánh xạ Tên Service sang Icon/Node Type
NODE_MAP = {
    'prometheus': Prometheus, 'grafana': Grafana, 'loki': Node, 'jaeger': Node,
    'kafka': Kafka, 'zookeeper': Zookeeper, 'redis': Redis, 'minio': Minio,
    'keycloak': Keycloak, 'spark-ui-proxy': Proxy, 'access-host-proxy': Proxy,
    'cadvisor': Server, 'promtail': Node, 'nginx-prometheus-exporter': Node, 
    'postgres': PostgreSQL, 'postgres-dwh': PostgreSQL, 'postgres-marquez': PostgreSQL,
    'spark-master': Rack, 'spark-worker': Rack, 'jupyterlab': Node,
    'ranger': Node, 'openlineage': Node, 'openmetadata': Node, 
    'airflow-webserver': Node, 'airflow-scheduler': Node, 'airflow-dag-processor': Node,
    'airflow-init': Node, 'flower': Node, 'kafka-client': Node,
}

# 3. Trích xuất Dependencies
dependencies = defaultdict(list)
for name, cfg in services.items():
    if 'depends_on' in cfg:
        deps = cfg['depends_on']
        if isinstance(deps, dict):
            dependencies[name].extend(deps.keys())
        elif isinstance(deps, list):
            dependencies[name].extend(deps)

# 4. Vẽ Sơ đồ
with Diagram(
    name="CDP - Full Stack Architecture Diagram", 
    show=False, 
    filename=output_filename, 
    direction="TB" # Top to Bottom
) as diag:
    
    # Khởi tạo các Cluster và Nodes
    clusters = defaultdict(lambda: Cluster(""))
    nodes = {}
    
    for name, group_name in SERVICE_GROUPS.items():
        if name in services:
            # Tạo Cluster (nếu chưa có)
            if group_name not in clusters:
                clusters[group_name] = Cluster(group_name)
            
            # Tạo Node bên trong Cluster
            node_type = NODE_MAP.get(name, Node)
            
            # Khác biệt: Spark, Airflow, OpenLineage/Metadata chưa có Icon cụ thể trong diagrams
            if group_name == 'Workflow Orchestration (Airflow)':
                 # Dùng icon PostgreSQL (backend) cho Airflow DB
                if name == 'postgres':
                    nodes[name] = PostgreSQL(name)
                elif name == 'redis':
                    nodes[name] = Redis(name)
                else: # Các services Airflow còn lại
                    nodes[name] = Node(name, icon="../airflow_icon.png") # Cần icon tùy chỉnh
            elif group_name == 'Data Processing (Spark)':
                 nodes[name] = Rack(name)
            elif name == 'openlineage':
                nodes[name] = Node("OpenLineage (Marquez)")
            elif name == 'openmetadata':
                nodes[name] = Node("OpenMetadata")
            else:
                 nodes[name] = node_type(name)
                 
            # Gán Node vào Cluster (không hoạt động trực tiếp trong Diagrams, cần dùng thủ công)
            # nodes[name] sẽ được vẽ trong ngữ cảnh hiện tại.
            
    # Tạo kết nối (Vẽ ra các edge)
    for source, targets in dependencies.items():
        source_node = nodes.get(source)
        if source_node:
            for target_name in targets:
                target_node = nodes.get(target_name)
                if target_node:
                    source_node >> target_node
    
    # Thêm các kết nối Logic/Dữ liệu (Không dùng depends_on)
    # Dữ liệu/Logs/Metrics Flow
    
    # 1. Observability: Promtail/cAdvisor -> Prometheus/Loki
    nodes['cadvisor'] >> nodes['prometheus']
    nodes['promtail'] >> nodes['loki']
    nodes['nginx-prometheus-exporter'] >> nodes['prometheus']
    
    # 2. Spark/Jupyter -> Master
    nodes['jupyterlab'] >> nodes['spark-master']
    nodes['spark-worker'] >> nodes['spark-master']
    
    # 3. Data Flow: Spark -> Kafka
    if 'spark-master' in nodes and 'kafka' in nodes:
        nodes['spark-master'] - nodes['kafka'] # Kết nối 2 chiều (Data In/Out)

    # 4. Lineage Flow: Airflow/Spark -> OpenLineage
    nodes['airflow-webserver'] >> nodes['openlineage']
    nodes['airflow-scheduler'] >> nodes['openlineage']
    nodes['spark-master'] >> nodes['openlineage']
    
    # 5. Metadata/Governance Flow
    nodes['openmetadata'] >> nodes['postgres-marquez']
    nodes['openmetadata'] >> nodes['minio']
    nodes['ranger'] >> nodes['postgres'] # Ranger dùng DB riêng
    
    # 6. Proxy
    nodes['spark-ui-proxy'] >> nodes['spark-master']
    
print(f"\nĐã tạo sơ đồ kiến trúc thành công: {output_filename}.png")
print("Sơ đồ đã cố gắng phân nhóm và thêm các kết nối logic. Vui lòng kiểm tra file hình ảnh.")