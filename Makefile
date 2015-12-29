all: blaster blastee

blaster: blaster.c
	gcc -o blaster blaster.c

blastee: blastee.c
	gcc -o blastee blastee.c

clean:
	rm -rf *.o blaster blastee
