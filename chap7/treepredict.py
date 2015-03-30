#!/usr/bin/env python
# -*- encoding=utf-8 -*-

import math
from PIL import Image, ImageDraw

my_data=[['slashdot','USA','yes',18,'None'],
        ['google','France','yes',23,'Premium'],
        ['digg','USA','yes',24,'Basic'],
        ['kiwitobes','France','yes',23,'Basic'],
        ['google','UK','no',21,'Premium'],
        ['(direct)','New Zealand','no',12,'None'],
        ['(direct)','UK','no',21,'Basic'],
        ['google','USA','no',24,'Premium'],
        ['slashdot','France','yes',19,'None'],
        ['digg','USA','no',18,'None'],
        ['google','UK','no',18,'None'],
        ['kiwitobes','UK','no',19,'None'],
        ['digg','New Zealand','yes',12,'Basic'],
        ['slashdot','UK','no',21,'None'],
        ['google','UK','yes',18,'Basic'],
        ['kiwitobes','France','yes',19,'Basic']]

class DecisionNode:
    def __init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col = col
        self.value = value
        self.results = results
        self.tb = tb
        self.fb = fb

# Divides a set on a specific column.
def divide_set(rows, column, value):
    split_function = None
    if isinstance(value, int) or \
            isinstance(value, float):
        split_function = lambda row: row[column] >= value
    else:
        split_function = lambda row: row[column] == value

    set1 = [row for row in rows if split_function(row)]
    set2 = [row for row in rows if not split_function(row)]
    return (set1, set2)

# Create counts of possivle results
def unique_counts(rows):
    result = {}
    for row in rows:
        r = row[len(row) - 1]
        if r not in result:
            result[r] = 0
        result[r] += 1
    return result

def gini_impurity(rows):
    total = len(rows)
    counts = unique_counts(rows)
    imp = 0.0

    for k1 in counts:
        p1 = float(counts[k1]) / total
        for k2 in counts:
            if k1 == k2:
                continue
            p2 = float(counts[k2]) / total
            imp += p1 * p2
    return imp

def entropy(rows):
    total = len(rows)
    counts = unique_counts(rows)
    en = 0.0
    for k in counts:
        p = float(counts[k]) / total
        en += p * math.log(p) / math.log(2)
    return -en

def build_tree(rows, scoref=entropy):
    if len(rows) == 0:
        return DecisionNode()
    
    current_score = scoref(rows)
    best_set1 = None
    best_set2 = None
    best_value = None
    best_column = None
    column_len = len(rows[0])
    for i in range(column_len-2):
        values = set([row[i] for row in rows])
        for value in values:
            set1, set2 = divide_set(rows, i, value)
            score1 = scoref(set1)
            score2 = scoref(set2)
            p = float(len(set1)) / len(rows)
            after_score = p * score1 + (1 - p) * score2
#            print 'c, a: %f, %f' % (current_score, after_score)
            if after_score < current_score:
                current_score = after_score
                best_set1 = set1
                best_set2 = set2
                best_value = value
                best_column = i
    if best_set1:
        return DecisionNode(value=best_value, col=best_column, tb=build_tree(best_set1, scoref=scoref), fb=build_tree(best_set2, scoref=scoref)) 
    else:
        return DecisionNode(results=unique_counts(rows)) 

def print_tree(tree, indent=''):
    if tree.results != None:
        print str(tree.results)
    else:
        print str(tree.col) + ':' + str(tree.value) + '?'
        print indent + 'T->', 
        print_tree(tree.tb, indent+ ' ')
        print indent + 'T->',
        print_tree(tree.fb, indent+ ' ')

def get_width(tree):
    if tree.results != None:
        return 1
    return get_width(tree.tb) + get_width(tree.fb)

def get_depth(tree):
    if tree.results != None:
        return 0
    return max(get_depth(tree.tb), get_depth(tree.fb)) + 1

def draw_tree(tree, jpeg='tree.jpeg'):
    w = get_width(tree) * 100
    h = get_depth(tree) * 100 + 120

    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw_node(draw, tree, w / 2, 20)
    img.save(jpeg, 'JPEG')

def draw_node(draw, tree, x, y):
    if tree.results == None:
        w1 = get_width(tree.fb) * 100
        w2 = get_width(tree.tb) * 100

        left = x - (w1 + w2) / 2
        right = x + (w1 + w2) / 2
        
        draw.text((x - 20, y - 10), str(tree.col)+':'+str(tree.value), (0, 0, 0))

        draw.line((x, y, left + w1 / 2, y + 100), fill=(255, 0, 0))
        draw.line((x, y, right - w2 / 2, y + 100), fill=(255, 0, 0))
        draw_node(draw, tree.fb, left + w1 / 2, y + 100)
        draw_node(draw, tree.tb, right - w2 / 2, y + 100)
    else:
        txt = '\n'.join(['%s:%d' % v for v in tree.results.items()])
        draw.text((x - 20, y), txt, (0, 0, 0))

def test():
    print divide_set(my_data, 2, 'yes')
    print unique_counts(my_data)
    print gini_impurity(my_data)
    print entropy(my_data)
    tree = build_tree(my_data)
    print_tree(tree)
    draw_tree(tree)
    
if __name__ == '__main__':
    test()

