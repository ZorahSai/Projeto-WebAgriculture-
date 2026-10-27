## 2. Opção A – Dataset real

<!-- O que foi encontrado sobre um dataset real de ICMP. Cite a fonte de cada informação. -->

Origem/link: Kaggle – "Network Traffic Dataset Captured through Wireshark", publicado por Deavanathan (https://www.kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark)
Formato: CSV (Captured_packets.csv, 16,28 MB), captura de pacotes via Wireshark em máquina Windows, interface Wi-Fi
Período coberto: não informado — apenas timestamps Epoch (Unix time)
Campos disponíveis: 19 colunas, incluindo time, src_ip, dst_ip, protocol, packet_length, tcp_src_port, tcp_dst_port, ttl, tcp_flags, window_size, ack_rtt (RTT real do ACK)
Licença: MIT

**Resumo do que foi encontrado:**

O dataset "Network Traffic Dataset Captured through Wireshark", disponível no Kaggle sob licença MIT, contém uma captura real de pacotes de rede feita via Wireshark em uma máquina Windows conectada por Wi-Fi, totalizando 19 colunas e um arquivo de 16,28 MB (Captured_packets.csv). O tráfego capturado é majoritariamente TCP (78%) e TLSv1.3 (18%), com protocolos de descoberta de serviço local como MDNS, SSDP e DHCP também presentes. Não há indicação de período/data da captura, apenas timestamps em Unix time. Fonte: Kaggle, aba "Data Card" do dataset "Network Traffic Dataset Captured through Wireshark" (kaggle.com/datasets/deavanathan/network-traffic-dataset-captured-through-wireshark), acessada em 08/09/2026.
