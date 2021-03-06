#!/usr/bin/env python3
import json
import os
import sys
import time

from flask import Flask, render_template, request

from classes import Graph, Node, Position

app = Flask('c3nav-config')

if 'C3NAVPROJECT' in os.environ:
    project = os.environ['C3NAVPROJECT']
elif len(sys.argv) > 1:
    project = sys.argv[1]
else:
    print('Please specify project: run.py <project> or environment variable C3NAVPROJECT')
    sys.exit(1)


@app.route('/')
def map():
    graph = Graph(project, auto_connect=True)
    return render_template('map.html', levels=graph.get_by_levels(), name=graph.name)


@app.route('/addroom', methods=['POST'])
def addroom():
    data = json.load(open('projects/'+project+'/graph.json'))
    data['rooms'][request.form.get('name')] = {
        'level': int(request.form.get('level')),
        'shape': request.form.get('shape')
    }

    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/addnode', methods=['POST'])
def addnode():
    data = json.load(open('projects/'+project+'/graph.json'))
    graph = Graph(project, auto_connect=False)

    level = int(request.form.get('level'))
    x = int(request.form.get('x'))
    y = int(request.form.get('y'))
    room = graph.get_room(Node(None, None, level, x, y))
    if room is None:
        return json.dumps({'success': False})

    newname = hex(int(time.time()*100))[2:]
    data['nodes'][newname] = {
        'level': level,
        'x': x,
        'y': y
    }
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)

    return json.dumps({
        'success': True,
        'name': newname,
        'room': room.name,
        'node': data['nodes'][newname]
    })


@app.route('/addpoi', methods=['POST'])
def addpoi():
    data = json.load(open('projects/'+project+'/pois.json'))
    graph = Graph(project, auto_connect=False)

    level = int(request.form.get('level'))
    x = int(request.form.get('x'))
    y = int(request.form.get('y'))
    name = request.form.get('name')
    room = graph.get_room(Position(level, x, y))
    if room is None:
        return json.dumps({'success': False})

    data[name] = {
        'level': level,
        'x': x,
        'y': y
    }
    json.dump(data, open('projects/'+project+'/pois.json', 'w'), indent=4, sort_keys=True)

    return 'ok'


@app.route('/addbarrier', methods=['POST'])
def addbarrier():
    data = json.load(open('projects/'+project+'/graph.json'))

    level = int(request.form.get('level'))
    x1 = int(request.form.get('x1'))
    y1 = int(request.form.get('y1'))
    x2 = int(request.form.get('x2'))
    y2 = int(request.form.get('y2'))

    data['barriers'].append({
        'level': level,
        'x1': x1,
        'y1': y1,
        'x2': x2,
        'y2': y2,
    })
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)

    return 'ok'


@app.route('/addconnection', methods=['POST'])
def addconnection():
    data = json.load(open('projects/'+project+'/graph.json'))
    graph = Graph(project, auto_connect=False)

    node1 = graph.nodes[graph.nodes_by_name[request.form.get('node1')]]
    node2 = graph.nodes[graph.nodes_by_name[request.form.get('node2')]]

    directed = request.form.get('directed') == '1'
    ctype = request.form.get('ctype')

    if graph.get_connection(node1, node2)[0] is not None:
        return json.dumps({'success': False})

    cdata = {
        'node0': request.form.get('node1'),
        'node1': request.form.get('node2'),
    }
    if ctype != 'default':
        cdata['ctype'] = ctype

    if directed:
        cdata['directed'] = True

    data['connections'].append(cdata)
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)

    return json.dumps({
        'success': True,
        'x1': node1.x,
        'y1': node1.y,
        'x2': node2.x,
        'y2': node2.y,
        'node1': node1.name,
        'node2': node2.name,
        'directed': directed,
        'ctype': ctype,
        'levels': list(set((node1.level, node2.level)))
    })


@app.route('/delnode', methods=['POST'])
def delnode():
    data = json.load(open('projects/'+project+'/graph.json'))
    name = request.form.get('name')
    data['nodes'].pop(name)
    data['connections'] = [c for c in data['connections'] if c['node0'] != name and c['node1'] != name]
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/delpoi', methods=['POST'])
def delpoi():
    data = json.load(open('projects/'+project+'/pois.json'))
    name = request.form.get('name')
    print(data)
    data.pop(name)
    json.dump(data, open('projects/'+project+'/pois.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/delconnection', methods=['POST'])
def delconnection():
    data = json.load(open('projects/'+project+'/graph.json'))
    nodes = (request.form.get('node1'), request.form.get('node2'))

    data['connections'] = [c for c in data['connections'] if c['node0'] not in nodes or c['node1'] not in nodes]
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/delroom', methods=['POST'])
def delroom():
    data = json.load(open('projects/'+project+'/graph.json'))
    room = request.form.get('room')
    data['rooms'].pop(room)
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


@app.route('/delbarrier', methods=['POST'])
def delbarrier():
    data = json.load(open('projects/'+project+'/graph.json'))
    level = int(request.form.get('level'))
    x1 = int(request.form.get('x1'))
    y1 = int(request.form.get('y1'))
    x2 = int(request.form.get('x2'))
    y2 = int(request.form.get('y2'))
    data['barriers'] = [b for b in data['barriers']
                        if b['level'] != level or b['x1'] != x1 or b['y1'] != y1 or b['x2'] != x2 or b['y2'] != y2]
    json.dump(data, open('projects/'+project+'/graph.json', 'w'), indent=4, sort_keys=True)
    return 'ok'


app.run(threaded=True, debug=True)
