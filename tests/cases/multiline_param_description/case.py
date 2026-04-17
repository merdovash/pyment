def func(param_file, mask):
    """
    :param lxml.etree.ElementTree param_file: xml-element tree
        obtained from the file.
    :param str mask: Name of mask to be considered.
    """
    pass


def func2(param1: str, param2):
    """
    :param str param1: description 1
    :param str param2: description 2
    :returns: description return
    """
    pass


def func3(param1: str, param2):
    """
    :param param1: description 1 is
        a multiline description
    :param str param2: description 2
    :returns: description return
    """
    pass


def func4(param1, param2):
    """
    :param param1: description 1
    :param str param2: description 2
    :returns: description return
    """
    pass


def func5(param1, param2):
    """
    :param int param1: description 1
    :param param2: description 2
    :returns: description return
    """
    pass


def func6(param1: list, param2):
    """
    :param int param1: description 1
    :param param2: description 2
    :returns: description return
    """
    pass


class Foo:
    """ Foo """
    def bar(self, arg_my: bool):
        """description description

        :param arg_my: description arg_my description arg_my description arg_my description arg_my
            description arg_my description arg_my description arg_my

        """
        return 


class DWCWrapper:
    """Универсальная обертка callback-вызовов в массовой операции.

    Что делает:
    - вызывает целевой BL-метод;
    - собирает ошибки/предупреждения в `Errors`;
    - сохраняет успешные результаты в `Results`;
    - формирует Excel по ошибкам и ссылку `ResultLink`;
    - публикует события (`SingleItemEvent`/`CallEvent`) при необходимости.

    Как "монада состояния":
    - вход: `(prev_result, options, args)`;
    - внутреннее состояние накапливается в полях экземпляра;
    - `call()` последовательно трансформирует состояние
      (`read -> invoke -> merge errors/results -> finalize`)
      и возвращает новый агрегированный `Record`.

    Основное внутреннее состояние:
    - `_errors: sbis.RecordSet`
      Накопленные ошибки/предупреждения по элементам.
    - `_rs: sbis.RecordSet | None`
      Накопленные успешные результаты целевого callback-метода.
    - `_has_errors: bool`
      Флаг "были строгие ошибки".
    - `_has_soft_errors: bool`
      Флаг "были мягкие предупреждения" (`MultipleDelayedDWCException`).
    - `_link: str | None`
      Ссылка на Excel-отчет по ошибкам.
    - `_result: sbis.Record`
      Текущее агрегированное значение (формат `get_result_format()`),
      которое возвращается наружу и может быть подано в следующий wrapper-вызов.

    Переходы состояния в `call()`:
    - `_read_previous_results`:
      если `prev_result` есть, подхватывает уже накопленные `Errors/Results/flags`;
      иначе инициализирует пустой набор ошибок.
    - `_call_inner_method`:
      выполняет callback (кроме `IsLast=True`), добавляет output в `_rs`,
      ошибки/предупреждения в `_errors` и обновляет флаги.
    - `_generate_excel`:
      при необходимости формирует Excel и заполняет `_link`.
    - `_generate_results`:
      собирает финальный `_result` из текущего состояния.
    - `_publish_event`:
      публикует финальное событие, состояние не меняет.
    """

    def __init__(self, prev_result: Record, options: Record, args: Record) -> None:
        """Initialize

        :param prev_result: sbis.Record | None
            Агрегированный результат предыдущего wrapper-вызова.
            Ожидаемый формат: `get_result_format()`, используются поля:
            - `Errors: RecordSet`
            - `Results: RecordSet`
            - `_HasStrictErrors: bool`
            - `_HasSoftErrors: bool`
        :param options: sbis.Record
            Конфигурация текущего шага wrapper.
            Обязательные/основные ключи:
            - `ObjectName: str`         имя BL-объекта callback-а
            - `MethodName: str`         имя BL-метода callback-а
            - `UntilFirstError: bool`   остановка после первой ошибки
            - `IsLast: bool`            флаг финального шага цепочки
            - `Fields: dict | Record`   поля для отчета ошибок/алиасы
            - `CallEvent: str`          финальное событие
            - `SingleItemEvent: str`    событие по одному успешному элементу
            - `ErrBack: Record`         обработчик ошибок
            - `EventOptions: dict|Record` (например `application`)
            - `DocumentLock: int`
            - `DocumentLockName: str`
            - `DocumentLockKey: str`
            - `PostProcessObject`, `PostProcessMethod`, `RaiseErrors`
              (используются наследниками, например `DWCAggregateWrapper`)
        :param args: sbis.Record
            Аргументы целевого BL-метода в "позиционной" упаковке:
            - `_arg1`, `_arg2`, ... `_argN`
            Порядок важен, вызов делается как:
            `Invoke(MethodName, *args.as_dict().values())`.
            В типовом массовом сценарии:
            - `_arg1`: документ (`sbis.Record`)
            - `_arg2`: фильтр callback-а (`sbis.Record`)
        :returns:

        """
        self._prev_result = prev_result
        self._options = options
        self._args = args