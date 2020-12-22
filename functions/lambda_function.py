import logging
import requests
import json
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    chatwork_apikey = os.environ['CHATWORK_APIKEY']     # 環境変数よりChatoworkAPIキー取得
    chatwork_roomid = os.environ['CHATWORK_ROOMID']     # 環境変数よりChatoworkルームID取得
    chatwork_endpoint = os.environ['CHATWORK_ENDPOINT'] # 環境変数よりChatoworkエンドポイント取得
    chatwork_header = os.environ['CHATWORK_HEADER']     # 環境変数よりChatoworkリクエストヘッダ取得

    # ハンドラーに渡されたイベントデータをロギング
    logger.info("EVENT: " + json.dumps(event))

    # イベントデータの一部を取得（Chatworkのメッセージに利用）
    subject = event['Records'][0]['Sns']['Subject']
    message = event['Records'][0]['Sns']['Message']

    # Chatworkに改行含めてjsonデータを連携するため文字列を辞書型に変換
    dict_message=json.loads(message)
    # indentオプション指定し改行等を保った状態でJSON形式にエンコード
    json_message = json.dumps(dict_message, indent=2)

    # EventBridge経由のイベントはsubjectが設定されていないのでメッセージ部より取得
    if subject is None:
        subject = dict_message['detail-type']

    # Chatwork指定のリクエストヘッダにAPIトークンを設定（リクエスト仕様）
    headers = {chatwork_header: chatwork_apikey}

    # SNSイベントよりChatworkメッセージ生成（インフォメーション + タイトル、絵文字無変換）
    chatwork_message = '[info][title]{0}[/title][code]{1}[/code][/info]'.format(subject,json_message)
    payload = {'body': chatwork_message}

    # Chatwork APIを利用するためのURL
    url = '{0}/rooms/{1}/messages'.format(chatwork_endpoint,chatwork_roomid)

    # Chatworkに投稿
    # paramsパラメータでのペイロードを指定するとクエリストリングとなり、Chatwork API（CloudFrontのURL最大長）の制限に抵触する恐れがあるのでdataパラメータを利用
    response = requests.post(url,headers=headers,data=payload)

    # ステータスコードを判定してロギング
    if response.status_code == requests.codes.ok:
        logger.info("Status Code :" + str(response.status_code) + " Response Header:" + json.dumps(dict(response.headers)))
        logger.info("Message posted to:" + str(chatwork_message))
        return {
            'statusCode': 200,
        }
    else:
        logger.error("Status Code :" + str(response.status_code) + " Response Header:" + json.dumps(dict(response.headers)))
        raise Exception