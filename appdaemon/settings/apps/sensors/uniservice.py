# -*- coding: utf-8 -*-
import os
import sys
import requests
import globals
import datetime as dt
import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, tzinfo, timedelta
from bs4 import BeautifulSoup

class EpdBalanceSensor(hass.Hass):
  login = ''
  pwd = ''
  accounts = []
  def initialize(self):
    # if not globals.check_properties(self,['login', 'pwd', 'accounts']):
    #   self.log('not enought params')
    #   return
    self.login = self.args.get('login', '')
    self.pwd = self.args.get('pwd', '')
    self.accounts = self.args.get('accounts', [])
    self.timer = self.run_every(self.update_sensors, self.datetime()+timedelta(seconds=1), 1*60*60)
    self.log(sys.stdout.encoding)
    self.log('привет мир')
    self.run_daily(self.send_counters_callback, "11:00:00", constrain_days = "sun")
    #self.send_counters_callback(None)

  def to_balance(self, value_str):
    value_str = value_str.replace(" ", "").replace(",", ".").replace("₽", "")
    return -1 * float(value_str)

  def update_sensors(self, args) -> None:
    entity_ids = self.args.get('entity_ids',[])
    session = self.get_auth_session(self.login, self.pwd)
    payment_amounts = self.get_payment_amounts(session, self.accounts)
    self.log(payment_amounts)

    fonvizina_epd_balance = self.to_balance(payment_amounts[0]['service_to_pay'])
    if 'fonvizina_epd_balance' in entity_ids:
      entity_id = entity_ids['fonvizina_epd_balance']
      attributes = {
          'unit_of_measurement': '₽',
          'icon': 'mdi:bank-transfer',
          'date': datetime.now().strftime('%d.%m.%Y'),
          'address': payment_amounts[0]['address'],
          'friendly_name': 'Баланс (ЕПД)',
          'description': 'Created and updated from appdaemon ({})'.format(__name__)
      }
      self.set_state(entity_id, state = fonvizina_epd_balance, attributes = attributes)

    fonvizina_trash_balance = self.to_balance(payment_amounts[0]['trash_to_pay'])
    if 'fonvizina_trash_balance' in entity_ids:
      entity_id = entity_ids['fonvizina_trash_balance']
      attributes = {
          'unit_of_measurement': '₽',
          'icon': 'mdi:bank-transfer',
          'date': datetime.now().strftime('%d.%m.%Y'),
          'address': payment_amounts[0]['address'],
          'friendly_name': 'Баланс Выввоз мусора',
          'description': 'Created and updated from appdaemon ({})'.format(__name__)
      }
      self.set_state(entity_id, state = fonvizina_trash_balance, attributes = attributes)

    fonvizina_kladovka_balance = self.to_balance(payment_amounts[1]['service_to_pay'])
    if 'fonvizina_kladovka_balance' in entity_ids:
      entity_id = entity_ids['fonvizina_kladovka_balance']
      attributes = {
          'unit_of_measurement': '₽',
          'icon': 'mdi:bank-transfer',
          'date': datetime.now().strftime('%d.%m.%Y'),
          'address': payment_amounts[1]['address'],
          'friendly_name': 'Баланс Кладовка',
          'description': 'Created and updated from appdaemon ({})'.format(__name__)
      }
      self.set_state(entity_id, state = fonvizina_kladovka_balance, attributes = attributes)

  def get_auth_session(self, phone, password):
      data={
          'AUTH_FORM': 'Y',
          'TYPE':'AUTH',
          'backurl': '/',
          'USER_LOGIN': phone,
          'USER_PASSWORD': password
      }
      r = requests.post('https://lkcab.ru/?login=yes', data=data, verify=False, allow_redirects=False)
      print(r.cookies)
      return r.cookies['PHPSESSID']

  def get_payment_amounts(self, session, accounts):
      cookies = dict(PHPSESSID=session)
      results = []
      for account in accounts:
          url = 'https://lkcab.ru/?accountID={}'.format(account)
          r = requests.get(url, cookies=cookies, verify=False)

          result = {}
          result['account'] = account

          doc = BeautifulSoup(r.content, 'html.parser')
          address = doc.find("div", string="Вы собственник по адресу:").parent.find_all('div')[1].text
          result['address'] = address
          
          service_to_pay = doc.find('div', string="ЖКУ, к оплате:").parent.find_all('div')[1].text.replace(' Р.', '')
          result['service_to_pay'] = service_to_pay

          trash_to_pay = '0'
          trash_to_pay_item = doc.find('div', string="Обращение с ТКО, к оплате:")
          self.log(trash_to_pay_item)
          if not trash_to_pay_item is None:
              trash_to_pay = trash_to_pay_item.parent.find_all('div')[3].text.replace(' Р.', '')
          result['trash_to_pay'] = trash_to_pay
          results.append(result)
      return results

  def send_counters_callback(self, kwargs) -> None:
    if 'constraint' in self.args and not self.constrain_input_boolean(self.args['constraint']):
      return
    self.log('sending counters....')
    session = self.get_auth_session(self.login, self.pwd)
    self.send_counters(session)
    return

  def send_counters(self, session) -> None:
      cookies = dict(PHPSESSID=session)
      account = self.accounts[0]
      url = 'https://lkcab.ru/?accountID={}'.format(account)
      r = requests.get(url, cookies=cookies, verify=False)

      url = 'https://lkcab.ru/counters/'
      r = requests.get(url, cookies=cookies, verify=False)
      doc = BeautifulSoup(r.content, 'html.parser')
      bitrix_session = doc.find("input", id="sessid").get('value')
      self.log('session: {}'.format(bitrix_session))

      data = {
        'action':'set_meters',
        'sessid': bitrix_session,
      }
      needToSend = False
      if 'heat_total' in self.args:
        needToSend = True
        value = self.get_state(self.args['heat_total'])
        if value != None:
          data['indiccur1[294174]'] = value

      if 'counter_cold_outer' in self.args:
        needToSend = True
        value = self.get_state(self.args['counter_cold_outer'])
        if value != None:
          data['indiccur1[294175]'] = value

      if 'counter_hot_outer' in self.args:
        needToSend = True
        value = self.get_state(self.args['counter_hot_outer'])
        if value != None:
          data['indiccur1[294173]'] = value

      if needToSend:
        self.log('sending: {}'.format(data))
        r = requests.post("https://lkcab.ru/counters/", cookies=cookies, data=data, verify=False)
        self.notify_tg("Показания отправлены в юнисервис. {}".format(data))
      self.log('done.')

  def notify_tg(self, msg):
    if not 'notify' in self.args:
      return
    extra_data = {'parse_mode': 'html'}
    self.notify(msg, name = self.args['notify'], data=extra_data)
