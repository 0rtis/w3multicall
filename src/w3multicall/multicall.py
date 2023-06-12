from typing import Tuple, List, Union, Optional, Any, Iterable, Callable

import eth_utils
from eth_typing.abi import Decodable, TypeStr

# For eth_abi versions < 2.2.0, `decode` and `encode` have not yet been added.
# As we require web3 ^5.27, we require eth_abi compatibility with eth_abi v2.0.0b6 and greater.
try:
    from eth_abi import decode, encode
except ImportError:
    from eth_abi import encode_abi as encode, decode_abi as decode


def _parse_signature(signature: str) -> Tuple[str, List[TypeStr], List[TypeStr]]:
    """
    Breaks 'func(address)(uint256)' into ['func', ['address'], ['uint256']]
    """
    parts: List[str] = []
    stack: List[str] = []
    start: int = 0
    for end, character in enumerate(signature):
        if character == '(':
            stack.append(character)
            if not parts:
                parts.append(signature[start:end])
                start = end
        if character == ')':
            stack.pop()
            if not stack:  # we are only interested in outermost groups
                parts.append(signature[start:end + 1])
                start = end + 1
    function = ''.join(parts[:2])
    input_types = _parse_type_string(parts[1])
    output_types = _parse_type_string(parts[2])
    return function, input_types, output_types


def _parse_type_string(typestring: str) -> Optional[List[TypeStr]]:
    if typestring == "()":
        return []
    parts = []
    part = ''
    inside_tuples = 0
    for character in typestring[1:-1]:
        if character == "(":
            inside_tuples += 1
        elif character == ")":
            inside_tuples -= 1
        elif character == ',' and inside_tuples == 0:
            parts.append(part)
            part = ''
            continue
        part += character
    parts.append(part)
    return parts


def _encode_data(selector, input_types: List[TypeStr], inputs) -> bytes:
    return selector + encode(input_types, inputs) if inputs else selector


def _decode_data(output_types: List[TypeStr], output: Decodable) -> Any:
    return decode(output_types, output)


def get_args(calls, require_success) -> List[Union[bool, List[List[Any]]]]:
    if require_success is True:
        return [[[call.address, call.data] for call in calls]]
    return [require_success, [[call.address, call.data] for call in calls]]


def _decode_output(
        output: Decodable,
        output_types: List[TypeStr],
        returns: Optional[Iterable[Tuple[str, Callable]]] = None,
        success: Optional[bool] = None
) -> Any:
    if success is None:
        apply_handler = lambda handler, value: handler(value)
    else:
        apply_handler = lambda handler, value: handler(success, value)

    if success is None or success:
        try:
            decoded = _decode_data(output_types, output)
        except:
            success, decoded = False, [None] * (1 if not returns else len(returns))  # type: ignore
    else:
        decoded = [None] * (1 if not returns else len(returns))  # type: ignore

    if returns:
        return {
            name: apply_handler(handler, value) if handler else value
            for (name, handler), value
            in zip(returns, decoded)
        }
    else:
        return decoded if len(decoded) > 1 else decoded[0]


def _unpack_aggregate_outputs(outputs: Any) -> Tuple[Tuple[Union[None, bool], bytes], ...]:
    return tuple((None, output) for output in outputs)


class W3Multicall:
    MULTICALL_METHOD_NAME, MULTICALL_INPUT_TYPES, MULTICALL_OUTPUT_TYPES = _parse_signature("aggregate((address,bytes)[])(uint256,bytes[])")
    MULTICALL_SELECTOR = eth_utils.function_signature_to_4byte_selector(MULTICALL_METHOD_NAME)

    class Call:
        def __init__(self, address: str, signature: str, args=None):
            self.address = address
            self.signature = signature.replace(" ", "")

            if args is not None and not isinstance(args, list) and not isinstance(args, tuple):
                self.args = (args,)
            else:
                self.args = args
            self.name, self.input_types, self.output_types = _parse_signature(signature)
            self.selector = eth_utils.function_signature_to_4byte_selector(self.name)
            self.data = _encode_data(self.selector, self.input_types, self.args)

    def __init__(self, w3, address='0xcA11bde05977b3631167028862bE2a173976CA11', calls: List['W3Multicall.Call'] = None):
        self.w3 = w3
        self.address = address
        self.calls: List['W3Multicall.Call'] = [] if calls is None else calls.copy()
        self.require_success = True

    def add(self, call: 'W3Multicall.Call'):
        self.calls.append(call)

    def call(self) -> list:
        args = self._get_args()
        data = _encode_data(W3Multicall.MULTICALL_SELECTOR, W3Multicall.MULTICALL_INPUT_TYPES, args)
        eth_call_params = {
            'to': self.address,
            'data': data
        }
        rpc_response = self.w3.eth.call(eth_call_params)
        aggregated = _decode_output(rpc_response, W3Multicall.MULTICALL_OUTPUT_TYPES)
        unpacked = _unpack_aggregate_outputs(aggregated[1])
        outputs = []
        for call, (success, output) in zip(self.calls, unpacked):
            call_output = _decode_output(output, call.output_types, None, True)
            outputs.append(call_output)
        return outputs

    def _get_args(self) -> List[Union[bool, List[List[Any]]]]:
        if self.require_success is True:
            return [[[call.address, call.data] for call in self.calls]]
        return [self.require_success, [[call.address, call.data] for call in self.calls]]
