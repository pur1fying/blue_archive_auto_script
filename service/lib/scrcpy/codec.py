import json
import struct
from typing import List, Optional, Iterator

START_CODE_3 = b"\x00\x00\x01"
START_CODE_4 = b"\x00\x00\x00\x01"


def find_nal_units_annexb(data: bytes) -> List[bytes]:
    """
    从 Annex-B 字节流中提取 NAL（保留 start code）。
    注意：这是对单个 buffer 的切分，不处理跨 buffer 的半截 NAL。
    """
    positions = []
    i = 0
    n = len(data)
    while i < n - 3:
        if data[i:i + 4] == START_CODE_4:
            positions.append(i)
            i += 4
        elif data[i:i + 3] == START_CODE_3:
            positions.append(i)
            i += 3
        else:
            i += 1

    if not positions:
        return []

    nals = []
    for idx, start in enumerate(positions):
        end = positions[idx + 1] if idx + 1 < len(positions) else len(data)
        nals.append(data[start:end])
    return nals


def strip_start_code(nal: bytes) -> bytes:
    if nal.startswith(START_CODE_4):
        return nal[4:]
    if nal.startswith(START_CODE_3):
        return nal[3:]
    return nal


def nal_type(nal: bytes) -> int:
    body = strip_start_code(nal)
    if not body:
        return -1
    return body[0] & 0x1F


def is_vcl_nal(t: int) -> bool:
    return t in (1, 5)  # non-IDR / IDR


def is_parameter_set(t: int) -> bool:
    return t in (7, 8)  # SPS / PPS


def contains_idr(frame_annexb: bytes) -> bool:
    for nal in find_nal_units_annexb(frame_annexb):
        if nal_type(nal) == 5:
            return True
    return False


class H264AnnexBFramer:
    """
    把 H264 Annex-B 连续流切成较适合前端解码的 access unit。
    这是工程上可用的简化版，不是完整 H264 语法解析器。
    """

    def __init__(self, max_fps: int):
        self.buffer = bytearray()
        self.pending_nals: List[bytes] = []
        self.last_sps: Optional[bytes] = None
        self.last_pps: Optional[bytes] = None
        self.frame_interval_us = int(1_000_000 / max(max_fps, 1))
        self._pts_us = 0

    def construct_return_val(self, frame_annexb: bytes) -> bytes:
        is_key = 1 if contains_idr(frame_annexb) else 0
        header = struct.pack(
            ">QB",
            self._pts_us,
            is_key
        )
        self._pts_us += self.frame_interval_us
        return header + frame_annexb

    def decode(self, chunk: bytes) -> Iterator[bytes]:
        self.buffer.extend(chunk)
        units = self._extract_complete_nals()

        for nal in units:
            t = nal_type(nal)
            if t == 7:
                self.last_sps = nal
            elif t == 8:
                self.last_pps = nal

            if is_vcl_nal(t):
                if self.pending_nals:
                    to_send = b"".join(self.pending_nals)
                    yield self.construct_return_val(to_send)
                    self.pending_nals = []

                # IDR 前把最新 SPS/PPS 带上，方便前端重建解码器或恢复
                if t == 5:
                    if self.last_sps:
                        self.pending_nals.append(self.last_sps)
                    if self.last_pps:
                        self.pending_nals.append(self.last_pps)

                self.pending_nals.append(nal)
            else:
                # SEI / SPS / PPS / AUD 等跟到当前帧里
                self.pending_nals.append(nal)

    def flush(self) -> Optional[bytes]:
        if self.pending_nals:
            frame = b"".join(self.pending_nals)
            self.pending_nals = []
            return frame
        return None

    def _extract_complete_nals(self) -> List[bytes]:
        """
        从 buffer 中提取“完整 NAL”。
        保留最后一个可能不完整的尾巴，等待下一批 chunk。
        """
        data = bytes(self.buffer)
        positions = []
        i = 0
        n = len(data)
        while i < n - 3:
            if data[i:i + 4] == START_CODE_4:
                positions.append(i)
                i += 4
            elif data[i:i + 3] == START_CODE_3:
                positions.append(i)
                i += 3
            else:
                i += 1

        if len(positions) < 2:
            return []

        units = []
        for idx in range(len(positions) - 1):
            start = positions[idx]
            end = positions[idx + 1]
            units.append(data[start:end])

        self.buffer = bytearray(data[positions[-1]:])
        return units
