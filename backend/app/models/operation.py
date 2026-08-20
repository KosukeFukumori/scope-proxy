from sqlmodel import Field, SQLModel


class Operation(SQLModel, table=True):
    """OpenAPIのoperationId単位のエンドポイント定義。

    権限はpath文字列ではなくoperation_idをキーにする
    (スキーマ変更でpath/methodが別エンドポイントに再利用された場合の権限誤継承を避けるため)。
    """

    __tablename__ = "operations"

    operation_id: str = Field(primary_key=True)
    method: str
    path: str
    summary: str | None = None
    is_active: bool = Field(default=True)
