#!/usr/bin/env python3
import json, requests, dominate, configparser, uwsgi, time
from dominate.tags import *
from cgi import parse_qs, escape

config = configparser.ConfigParser()
configFile = uwsgi.magic_table[b'p'].decode('ascii')
print('using %s'%(configFile))
config.read(configFile)
settings = {}

def init():
    #web
    settings['sitename']              = config.get('web', 'sitename')
    settings['url']                   = config.get('web', 'url')
    #data
    settings['docroot']               = config.get('data', 'docroot')
    #api
    settings['api']                   = {}
    settings['api']['bic']            = config.get('api', 'bic')
    #api-vtc
    settings['api']['vtc']            = {}
    settings['api']['vtc']['p2pool']  = config.get('api-vtc', 'p2pool')
    settings['api']['vtc']['bic']     = config.get('api-vtc', 'bic')
    settings['api']['vtc']['ins']     = {}
    settings['api']['vtc']['ins']['wal'] = config.get('api-vtc', 'insight-wallet')
    settings['api']['vtc']['ins']['tx']  = config.get('api-vtc', 'insight-trans')

def application(env, start_response):
    vars = parse_qs(env['QUERY_STRING'])
    site = {}
    site['main'] = html(lang='en')
    site['head'] = site['main'].add(head())
    site['head'].add(link(href='https://woovie.net/coininfo/css/bootstrap.min.css', rel='stylesheet'))
    site['head'].add(script(src='https://woovie.net/coininfo/js/popper.js'))
    site['head'].add(script(src='https://woovie.net/coininfo/js/jquery.min.js'))
    site['head'].add(script(src='https://woovie.net/coininfo/js/bootstrap.min.js'))
    site['head'].add(title('% s | home'%(settings['sitename'])))
    site['body'] = site['main'].add(body())
    site['container'] = site['body'].add(div(cls='container'))
    if not vars.get('vtc'):
        site['container'].add(div(h1('welcome to %s'%(settings['sitename']), cls='display-3'), p('Put your wallet ID below', cls='lead'), cls='jumbotron'))
        site['container'].add(form(div(label('VTC Wallet ID'), input(cls='form-control', id='vtcID', name='vtc', placeholder='Wallet ID'), cls='form-group'), button('Submit', type='submit', cls='btn btn-primary'), action='/coin'))
        output = site['main'].render()
        start_response('200 OK', [('Content-Type','text/html')])
        yield output.encode()
    elif vars.get('vtc'):
        wallet = {}
        wallet['id'] = vars.get('vtc')[0]
        wallet['data'] = requests.get('%s%s'%(settings['api']['vtc']['ins']['wal'],  wallet['id'])).json()
        site['container'].add(div(h1('Wallet stats', cls='display-3'), p('wallet ID %s'%(wallet['id']), cls='lead'), cls='jumbotron'))
        wallet['transactions'] = {}
        site['transactions'] = site['container'].add(div(id='transactions'))
        site['transactions'].add(h2('Transactions'))
        site['transactions'].add(p('All transactions are GMT'))
        site['transactions'].add(p('Total Transactions: %s'%(len(wallet['data']['transactions']))))
        site['mhs_average'] = site['transactions'].add(p())
        site['time_avgerage'] = site['transactions'].add(p())
        wallet['previous'] = ''
        wallet['hourstamps'] = []
        for transaction in wallet['data']['transactions']:
            wallet['transactions'][transaction] = requests.get('%s%s'%(settings['api']['vtc']['ins']['tx'], transaction)).json()
        for transaction in wallet['transactions']:
            if len(wallet['previous']) != 0:
                wallet['hourstamps'].append(round((wallet['transactions'][wallet['previous']]['time'] - wallet['transactions'][transaction]['time']) / 3600, 2))
            date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(wallet['transactions'][transaction]['time']))
            site['transactions'].add(div(h5('Transaction ID %s'%(transaction)), p('Transaction date: %s'%(date)), cls='transaction'))
            wallet['previous'] = transaction
        
        site['time_avgerage'].add('Payout frequency average: %s'%())
        output = site['main'].render()
        start_response('200 OK', [('Content-Type','text/html')])
        yield output.encode()
init()
