#include<stdio.h> 
#include<string.h> 
#include<stdlib.h>
#include<unistd.h>
#include<ctype.h>
#include<arpa/inet.h>
#include<sys/socket.h>
#include<time.h>
 
//#define SERVER "127.0.0.1"
//#define BUFLEN 512  //Max length of buffer
//#define PORT 8888   //The port on which to send data
#define MAX_PACKET_SIZE 50000

struct header {
    char packet_type;
    uint32_t seq_num;
    uint32_t packet_len;
    char *payload;
};

void die(char *s)
{
    perror(s);
    exit(1);
}

void dump_packet(struct header *pkt) {
    
    printf("\nPkt_Type %c  Sequence Number: %d Packet Len %d Payload: %s",
           pkt->packet_type, ntohl(pkt->seq_num), ntohl(pkt->packet_len), pkt->payload);
}

int main(int argc, char *argv[])
{
    struct sockaddr_in si_other;
    int s, i, slen=sizeof(si_other);
    int c=0, hport=0, hrate=0, hnumpkts=0, hseq=0, hlen=0, hc=0;
    char *hostname = NULL;
    //char buf[BUFLEN] = "\0" ;
    int packet_size = 0, Hlen = 0;
    char ch = 'A';
    useconds_t usec;
    char *fillPayload;
    
    /* Get the Command line Arguments */
    while( (c = getopt(argc, argv, "s:p:r:n:q:l:c:")) != -1) {
        switch(c) {
            case 's':
                hostname = optarg;
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

    // Print the values
    printf("Hostname %s Port %d Rate %d Num of Pkts %d Seq Num: %d Payload Length: %d Echo %d\n",hostname, 
            hport, hrate, hnumpkts, hseq, hlen, hc); 

    /* Sanity Check for port and length */
    if(hport < 1024 && hport > 65536) {
        printf("Error: Given Port Number is Wrong.\n");
        exit(1);
    }
    if(hlen >= 50) {
        printf("Error: Payload more than 50 KB\n");
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
    while(hnumpkts > 0)
    {
        /* Generate Packet */
        struct header *pkt = (struct header *) malloc(sizeof(struct header));
        
        /* Fill the packet header */
        pkt->packet_type = 'D';
        pkt->seq_num = htonl(hseq);
        pkt->packet_len = htonl(hlen);
        //pkt->seq_num = hseq;
        //pkt->packet_len = hlen;

        pkt->payload = malloc(sizeof(hlen));
        fillPayload = pkt->payload;
    
        /* Fill the payload with length hlen as given in argument */
        while(hlen > 0) {
            *fillPayload = ch;
            //printf("%c ",*fillPayload);
            ch++; fillPayload++;
            hlen--;
        }

        packet_size = sizeof(struct header) + Hlen;
        //printf("Packet Size is %d + %ld \n ",packet_size, sizeof(struct header));

        /* Print the packet */
        dump_packet(pkt);
    
        //send the message
        if (sendto(s, pkt, packet_size, 0 ,(struct sockaddr *)&si_other, slen) != -1) {
            printf("\nWaiting for %d millisec...",usec/1000);
            usleep(usec);
        } else {
            printf("Error: In Send Packet");
            die("sendto()");
        }
        
        /*
        //receive a reply and print it
        //clear the buffer by filling null, it might have previously received data
        memset(buf,'\0', BUFLEN);
        //try to receive some data, this is a blocking call
        if (recvfrom(s, buf, BUFLEN, 0, (struct sockaddr *) &si_other, &slen) == -1)
        {
            die("recvfrom()");
        }
         
        puts(buf);
        */

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
            pkt->payload = NULL;
        
            /* Print the packet */
            dump_packet(pkt);
            
            if (sendto(s, pkt, packet_size, 0 ,(struct sockaddr *)&si_other, slen) == -1) {
                printf("Error: In Send End Packet");
                die("sendto()");
            }
        }
        //free(pkt->payload);
        free(pkt);
        
    }
    printf("\n\n"); 
    close(s);
    return 0;
}
