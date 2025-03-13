# モデル定義をインポート
# 循環参照を解決するために、最初に個別のモデルをインポートしてから
# リレーションシップを解決します

from app.models.user import User
from app.models.item import Item