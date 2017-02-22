#ifndef LIST_H
#define LIST_H

typedef struct node{
    void *val;
    struct node *next;
    struct node *prev;
} node;

typedef struct darknet_list{
    int size;
    node *front;
    node *back;
} darknet_list;

darknet_list *make_list();
int list_find(darknet_list *l, void *val);

void list_insert(darknet_list *, void *);

void **list_to_array(darknet_list *l);

void free_list(darknet_list *l);
void free_list_contents(darknet_list *l);

#endif
