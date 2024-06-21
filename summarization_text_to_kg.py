import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def generate_knowledge_graph_images(kg_result):
    images = []
    for result in kg_result:
        graph = result.get('G')
        if graph is not None:
            plt.figure(figsize=(6, 6))
            pos = nx.spring_layout(graph)
            nx.draw(graph, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos=pos)
            nx.draw_networkx_edge_labels(graph, pos=pos)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            images.append(image_base64)
            plt.close()
    return images