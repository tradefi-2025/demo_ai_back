#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "type_pile.h"

void creer_pile(PileEntiers *p){
    p->n=0;
}
int est_vide(PileEntiers *p){
    return p->n == 0;
}
int sommet(PileEntiers *p){
    return p->tab[(p->n)-1];
}
int taille(PileEntiers *p){
    return p->n;
}
void print(PileEntiers *p){
    for(int i=0;i<p->n;i++){
        printf("%d",p->tab[i]);
    }
}

void vider(PileEntiers *p){
    p->n=0;
}

void empiler(PileEntiers *p, int x){
    if(p->n < TAILLE_MAX){
        p->tab[p->n]=x;
        p->n++;
    }
}
int depiler(PileEntiers *p){
    if(!est_vide(p)){
        p->n--;
        return p->tab[p->n];
    }
    
}
