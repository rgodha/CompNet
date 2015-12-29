#include<stdio.h> 
#include<string.h> 
#include<stdlib.h>
#include<unistd.h>
#include<ctype.h>
#include<arpa/inet.h>
#include<sys/socket.h>
#include<time.h>
#include<fcntl.h>
#include <netdb.h>
 
//#define SERVER "127.0.0.1"
#define BUFLEN 50100  //Max length of buffer
//#define PORT 8888   //The port on which to send data
#define MAX_PACKET_SIZE 50100

struct __attribute__((packed)) header {
    char packet_type;
    uint32_t seq_num;
    uint32_t packet_len;
};

void die(char *s)
{
    perror(s);
    exit(1);
}

void dump_packet(struct header *pkt)
{    
    printf("\nPkt_Type %c  Sequence Number: %d Packet Len %d  ",
           pkt->packet_type, ntohl(pkt->seq_num), ntohl(pkt->packet_len));
}

int main(int argc, char *argv[])
{
    struct sockaddr_in si_other;
    int s, i, slen=sizeof(si_other);
    int c=0, hport=0, hrate=0, hnumpkts=0, hseq=0, hlen=0, hc=0;
    char *hostname = NULL;
    char buf[BUFLEN] = "\0" ;
    int packet_size = 0, Hlen = 0, rv, recv_len;
    char ch = 'A';
    useconds_t usec;
    char *packet, *payload;
    int exp_payload_size = 0;
    struct hostent * he;
    struct in_addr **addr_list;
    
    /* Get the Command line Arguments */
    while( (c = getopt(argc, argv, "s:p:r:n:q:l:c:")) != -1) {
        switch(c) {
            case 's':
                //hostname = optarg;
                if ((he = gethostbyname(optarg)) == NULL ) {  // get the host info
                    herror("gethostbyname");
                    return 2;
                }   

                // print information about this host:
                //printf("Official name is: %s\n", he->h_name); 
                break;
            case 'p':
                hport = atoi(optarg);
                break;
            case 'r':
                hrate = atoi(optarg);
                break;
            case 'n':
                hnumpkts = atoi(optarg);
                break; 
            case 'q':
                hseq = atoi(optarg);
                break;
            case 'l':
                hlen = atoi(optarg);
                break;
            case 'c':
                hc = atoi(optarg);
                break;
            default: /* '?' */
                fprintf(stderr, "Usage: %s -s <hostname> -p <port> -r <rate> -n <num> -q " 
                                            "<seq_no> -l <length> -c <echo>\n", argv[0]);
                exit(1);
        }
    }
    
    if (optind > argc) {
        fprintf(stderr, "Expected less arguments\n");
        exit(1);
    }
    
    addr_list = (struct in_addr **)he->h_addr_list;
    for(i = 0; addr_list[i] != NULL; i++) {
        //printf("%s ", inet_ntoa(*addr_list[i]));
        hostname = inet_ntoa(*addr_list[i]);
    }

    // Print the values
    printf("Hostname %s Port %d Rate %d Num of Pkts %d Seq Num: %d Payload Length: %d Echo %d\n",hostname, 
            hport, hrate, hnumpkts, hseq, hlen, hc); 

    /* Sanity Check for port and length */
    if(hport < 1024 && hport > 65536) {
        printf("Error: Given Port Number is Wrong.\n");
        exit(1);
    }
    if(hlen >= 50000) {
        printf("Error: Payload more than 49999 B\n");
        exit(1);
    }

    /* Sending Rate for the packets */
    if(hrate == 0) {
        usec = 0;
    } else {
        usec = 1000000/hrate;
    }

    /* Socket Connections */
    if ((s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        die("socket");
    }

    memset((char *) &si_other, 0, sizeof(si_other));
    si_other.sin_family = AF_INET;
    si_other.sin_port = htons(hport);
     
    if (inet_aton(hostname, &si_other.sin_addr) == 0) 
    {
        fprintf(stderr, "inet_aton() failed\n");
        exit(1);
    }
 
    Hlen = hlen;    // For saving the payload length.
    
    packet = malloc(MAX_PACKET_SIZE);

    while(hnumpkts > 0)
    {
        /* Generate Packet */
        memset(packet, 0, MAX_PACKET_SIZE); 
        struct header *pkt = (struct header*) packet;

        /* Fill the packet header */
        pkt->packet_type = 'D';
        pkt->seq_num = htonl(hseq);
        pkt->packet_len = htonl(hlen);

        payload = packet + sizeof(struct header);

        packet_size = sizeof(struct header) + Hlen;

        /* Print the packet */
        dump_packet(pkt);
                if(Hlen == 0) {
                    printf("No Payload. ");
                } else if(Hlen == 1) {
                    printf("Payload: %02x ",payload[0]);
                } else if(Hlen == 2) {
                    printf("Payload: %02x%02x ",payload[0],payload[1]);
                } else if(Hlen == 3) {
                    printf("Payload: %02x%02x%02x ",payload[0],payload[1],payload[2]);
                } else {
                    printf("Payload: %02x%02x%02x%02x ",payload[0], payload[1],payload[2],payload[3]);
                } 


        //send the message
        if (sendto(s, packet, packet_size, 0 ,(struct sockaddr *)&si_other, slen) != -1) {
            printf("\nWaiting for %d millisec...",usec/1000);
            usleep(usec);
        } else {
            printf("Error: In Send Packet");
            die("sendto()");
        }

        memset(buf,'\0', BUFLEN);
        //try to receive some data, this is a blocking call
        if(hc == 1) {
        if (recvfrom(s, buf, BUFLEN, MSG_DONTWAIT, (struct sockaddr *) &si_other, &slen) != -1) 
        {
                struct header *pkt;
    
                pkt = (struct header *)buf;
                payload = buf + sizeof(struct header);
                if(pkt->packet_type == 'C')
                    printf("\nECHO: ");

                exp_payload_size = ntohl(pkt->packet_len);
                dump_packet(pkt);
                if(exp_payload_size == 0) {
                    printf("No Payload Received. ");
                } else if(exp_payload_size == 1) {
                    printf("Payload: %02x ",payload[0]);
                } else if(exp_payload_size == 2) {
                    printf("Payload: %02x%02x ",payload[0],payload[1]);
                } else if(exp_payload_size == 3) {
                    printf("Payload: %02x%02x%02x ",payload[0],payload[1],payload[2]);
                } else {
                    printf("Payload: %02x%02x%02x%02x ",payload[0], payload[1],payload[2],payload[3]);
                } 
        }
        }
        /* Reinitialize variable */
        hlen = Hlen;
        hseq += hlen; 
        //ch = 'A';
        hnumpkts--;
        
        /* When hnumpkts == 0: Send the END packet */
        if(hnumpkts == 0) {    
            pkt->packet_type = 'E';
            pkt->seq_num = htonl(hseq);
            packet_size = (int)(sizeof(struct header));
            pkt->packet_len = htonl(0);
            //pkt->payload = NULL;
        
            /* Print the packet */
            dump_packet(pkt);
            
            if (sendto(s, pkt, packet_size, 0 ,(struct sockaddr *)&si_other, slen) == -1) {
                printf("Error: In Send End Packet");
                die("sendto()");
            }
        }
        //free(pkt);
       
    }
       
    printf("\n\n"); 
    close(s);
    return 0;
}
