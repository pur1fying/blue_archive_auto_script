# import struct
# from typing import List, Optional, Iterator
#
# START_CODE_3 = b"\x00\x00\x01"
# START_CODE_4 = b"\x00\x00\x00\x01"
#
#
# def find_nal_units_annexb(data: bytes) -> List[bytes]:
#     """
#     从 Annex-B 字节流中提取 NAL（保留 start code）。
#     注意：这是对单个 buffer 的切分，不处理跨 buffer 的半截 NAL。
#     """
#     positions = []
#     i = 0
#     n = len(data)
#     while i < n - 3:
#         if data[i:i + 4] == START_CODE_4:
#             positions.append(i)
#             i += 4
#         elif data[i:i + 3] == START_CODE_3:
#             positions.append(i)
#             i += 3
#         else:
#             i += 1
#
#     if not positions:
#         return []
#
#     nals = []
#     for idx, start in enumerate(positions):
#         end = positions[idx + 1] if idx + 1 < len(positions) else len(data)
#         nals.append(data[start:end])
#     return nals
#
#
# def strip_start_code(nal: bytes) -> bytes:
#     if nal.startswith(START_CODE_4):
#         return nal[4:]
#     if nal.startswith(START_CODE_3):
#         return nal[3:]
#     return nal
#
#
# def nal_type(nal: bytes) -> int:
#     body = strip_start_code(nal)
#     if not body:
#         return -1
#     return body[0] & 0x1F
#
#
# def is_vcl_nal(t: int) -> bool:
#     return t in (1, 5)  # non-IDR / IDR
#
#
# def is_parameter_set(t: int) -> bool:
#     return t in (7, 8)  # SPS / PPS
#
#
# def contains_idr(frame_annexb: bytes) -> bool:
#     for nal in find_nal_units_annexb(frame_annexb):
#         if nal_type(nal) == 5:
#             return True
#     return False
#
#
# class H264AnnexBFramer:
#     """
#     把 H264 Annex-B 连续流切成较适合前端解码的 access unit。
#     这是工程上可用的简化版，不是完整 H264 语法解析器。
#     """
#
#     def __init__(self, max_fps: int):
#         self.buffer = bytearray()
#         self.pending_nals: List[bytes] = []
#         self.last_sps: Optional[bytes] = None
#         self.last_pps: Optional[bytes] = None
#         self.frame_interval_us = int(1_000_000 / max(max_fps, 1))
#         self._pts_us = 0
#
#     def construct_return_val(self, frame_annexb: bytes) -> bytes:
#         is_key = 1 if contains_idr(frame_annexb) else 0
#         header = struct.pack(
#             ">BQ",
#             is_key,
#             self._pts_us
#         )
#         self._pts_us += self.frame_interval_us
#         return header + frame_annexb
#
#     def decode(self, chunk: bytes) -> Iterator[bytes]:
#         self.buffer.extend(chunk)
#         units = self._extract_complete_nals()
#
#         for nal in units:
#             t = nal_type(nal)
#             if t == 7:
#                 self.last_sps = nal
#             elif t == 8:
#                 self.last_pps = nal
#
#             if is_vcl_nal(t):
#                 if self.pending_nals:
#                     to_send = b"".join(self.pending_nals)
#                     yield self.construct_return_val(to_send)
#                     self.pending_nals = []
#
#                 # IDR 前把最新 SPS/PPS 带上，方便前端重建解码器或恢复
#                 if t == 5:
#                     if self.last_sps:
#                         self.pending_nals.append(self.last_sps)
#                     if self.last_pps:
#                         self.pending_nals.append(self.last_pps)
#
#                 self.pending_nals.append(nal)
#             else:
#                 # SEI / SPS / PPS / AUD 等跟到当前帧里
#                 self.pending_nals.append(nal)
#
#     def flush(self) -> Optional[bytes]:
#         if self.pending_nals:
#             frame = b"".join(self.pending_nals)
#             self.pending_nals = []
#             return frame
#         return None
#
#     def _extract_complete_nals(self) -> List[bytes]:
#         """
#         从 buffer 中提取“完整 NAL”。
#         保留最后一个可能不完整的尾巴，等待下一批 chunk。
#         """
#         data = bytes(self.buffer)
#         positions = []
#         i = 0
#         n = len(data)
#         while i < n - 3:
#             if data[i:i + 4] == START_CODE_4:
#                 positions.append(i)
#                 i += 4
#             elif data[i:i + 3] == START_CODE_3:
#                 positions.append(i)
#                 i += 3
#             else:
#                 i += 1
#
#         if len(positions) < 2:
#             return []
#
#         units = []
#         for idx in range(len(positions) - 1):
#             start = positions[idx]
#             end = positions[idx + 1]
#             units.append(data[start:end])
#
#         self.buffer = bytearray(data[positions[-1]:])
#         return units
#
#
# class H264FMP4Framer:
#     """
#     Convert a continuous Annex-B H.264 byte stream into fragmented MP4 segments.
#
#     Output packet layout:
#         [is_key: 1 byte][pts_us: 8 bytes][segment payload]
#
#     Segment emission policy:
#     - The first valid video configuration produces one init segment.
#     - Each decoded access unit then produces one media segment (moof + mdat).
#     - If SPS/PPS changes later, a new init segment is emitted before the next
#       keyframe media segment.
#
#     Notes:
#     - This is a practical low-latency single-track implementation.
#     - It is not a full H.264 / ISO-BMFF reference implementation.
#     - It assumes no B-frames, so DTS == PTS.
#     """
#
#     class _BitReader:
#         """Minimal bit reader for SPS parsing."""
#
#         def __init__(self, data: bytes):
#             self.data = data
#             self.bitpos = 0
#
#         def read_bit(self) -> int:
#             if self.bitpos >= len(self.data) * 8:
#                 return 0
#             byte_idx = self.bitpos // 8
#             bit_idx = 7 - (self.bitpos % 8)
#             self.bitpos += 1
#             return (self.data[byte_idx] >> bit_idx) & 1
#
#         def read_bits(self, n: int) -> int:
#             v = 0
#             for _ in range(n):
#                 v = (v << 1) | self.read_bit()
#             return v
#
#         def read_ue(self) -> int:
#             zeros = 0
#             while self.read_bit() == 0:
#                 zeros += 1
#             if zeros == 0:
#                 return 0
#             return (1 << zeros) - 1 + self.read_bits(zeros)
#
#         def read_se(self) -> int:
#             code_num = self.read_ue()
#             if code_num & 1:
#                 return (code_num + 1) // 2
#             return -(code_num // 2)
#
#     def __init__(self, max_fps: int):
#         """
#         Initialize the fragmented MP4 framer.
#
#         Internally, this class reuses H264AnnexBFramer to:
#         - split the raw Annex-B stream into access units
#         - assign monotonically increasing timestamps
#         """
#         self.au_framer = H264AnnexBFramer(max_fps)
#
#         self.last_sps: Optional[bytes] = None
#         self.last_pps: Optional[bytes] = None
#
#         self.init_sps: Optional[bytes] = None
#         self.init_pps: Optional[bytes] = None
#
#         self.track_id = 1
#         self.sequence_number = 1
#
#         # Use microseconds as MP4 timescale to match the existing transport PTS.
#         self.timescale = 1_000_000
#         self.frame_duration = int(1_000_000 / max(max_fps, 1))
#
#         self.width = 640
#         self.height = 360
#
#         self.init_sent = False
#
#     def decode(self, chunk: bytes) -> Iterator[bytes]:
#         """
#         Feed raw Annex-B bytes and emit one or more fMP4 packets.
#
#         Each yielded packet still follows the transport header convention:
#             [is_key:1][pts_us:8][segment_bytes]
#
#         The first valid stream configuration yields an init segment first.
#         """
#         for packet in self.au_framer.decode(chunk):
#             is_key, pts_us = struct.unpack(">BQ", packet[:9])
#             frame_annexb = packet[9:]
#
#             nals = find_nal_units_annexb(frame_annexb)
#             if not nals:
#                 continue
#
#             has_idr = False
#             for nal in nals:
#                 t = nal_type(nal)
#                 if t == 7:
#                     self.last_sps = nal
#                     try:
#                         self.width, self.height = self._parse_sps_size(nal)
#                     except Exception:
#                         # Keep the previous size if SPS parsing fails.
#                         pass
#                 elif t == 8:
#                     self.last_pps = nal
#                 elif t == 5:
#                     has_idr = True
#
#             # Do not emit media segments before SPS/PPS is known.
#             if self.last_sps is None or self.last_pps is None:
#                 continue
#
#             # Emit a new init segment if:
#             # 1) we have never emitted one before, or
#             # 2) SPS/PPS changed and we are at a clean keyframe boundary.
#             need_new_init = (
#                 (not self.init_sent)
#                 or (
#                     has_idr
#                     and (
#                         self.init_sps != self.last_sps
#                         or self.init_pps != self.last_pps
#                     )
#                 )
#             )
#
#             if need_new_init:
#                 init_segment = self._build_init_segment(self.last_sps, self.last_pps)
#                 self.init_sps = self.last_sps
#                 self.init_pps = self.last_pps
#                 self.init_sent = True
#
#                 # Init segment is marked as key to make downstream handling simpler.
#                 yield self._wrap_packet(True, pts_us, init_segment)
#
#             sample_nals = [
#                 strip_start_code(nal)
#                 for nal in nals
#                 if nal_type(nal) not in (7, 8, 9)  # SPS / PPS / AUD
#             ]
#             if not sample_nals:
#                 continue
#
#             sample_data = self._annexb_nals_to_avcc(sample_nals)
#             media_segment = self._build_media_segment(
#                 sample_data=sample_data,
#                 pts_us=pts_us,
#                 is_key=bool(has_idr or is_key),
#             )
#
#             yield self._wrap_packet(bool(has_idr or is_key), pts_us, media_segment)
#
#     def _wrap_packet(self, is_key: bool, pts_us: int, payload: bytes) -> bytes:
#         """Wrap one MP4 segment with the existing transport header."""
#         header = struct.pack(">BQ", 1 if is_key else 0, pts_us)
#         return header + payload
#
#     def _annexb_nals_to_avcc(self, nals: List[bytes]) -> bytes:
#         """
#         Convert a list of raw NAL payloads (without start code) into AVCC sample format:
#             [length][nal][length][nal]...
#         """
#         out = bytearray()
#         for nal in nals:
#             out.extend(struct.pack(">I", len(nal)))
#             out.extend(nal)
#         return bytes(out)
#
#     def _build_avcc(self, sps: bytes, pps: bytes) -> bytes:
#         """
#         Build AVCDecoderConfigurationRecord (avcC) from SPS/PPS.
#         """
#         sps_body = strip_start_code(sps)
#         pps_body = strip_start_code(pps)
#
#         if len(sps_body) < 4:
#             raise ValueError("Invalid SPS for avcC")
#
#         out = bytearray()
#         out.append(0x01)  # configurationVersion
#         out.append(sps_body[1])  # AVCProfileIndication
#         out.append(sps_body[2])  # profile_compatibility
#         out.append(sps_body[3])  # AVCLevelIndication
#         out.append(0xFF)  # lengthSizeMinusOne = 3 (4 bytes)
#         out.append(0xE1)  # numOfSequenceParameterSets = 1
#
#         out.extend(struct.pack(">H", len(sps_body)))
#         out.extend(sps_body)
#
#         out.append(0x01)  # numOfPictureParameterSets = 1
#         out.extend(struct.pack(">H", len(pps_body)))
#         out.extend(pps_body)
#
#         return bytes(out)
#
#     def _build_init_segment(self, sps: bytes, pps: bytes) -> bytes:
#         """
#         Build the MP4 initialization segment: ftyp + moov.
#         """
#         avcc = self._build_avcc(sps, pps)
#
#         ftyp = self._box(
#             b"ftyp",
#             b"isom",
#             struct.pack(">I", 0x00000200),
#             b"isom",
#             b"iso6",
#             b"mp41",
#         )
#
#         avc1 = self._box(
#             b"avc1",
#             b"\x00" * 6,  # reserved
#             struct.pack(">H", 1),  # data_reference_index
#             struct.pack(">H", 0),  # pre_defined
#             struct.pack(">H", 0),  # reserved
#             b"\x00" * 12,  # pre_defined[3]
#             struct.pack(">H", self.width),
#             struct.pack(">H", self.height),
#             struct.pack(">I", 0x00480000),  # horizresolution = 72 dpi
#             struct.pack(">I", 0x00480000),  # vertresolution = 72 dpi
#             struct.pack(">I", 0),  # reserved
#             struct.pack(">H", 1),  # frame_count
#             b"\x00" * 32,  # compressorname
#             struct.pack(">H", 0x0018),  # depth
#             struct.pack(">H", 0xFFFF),  # pre_defined = -1
#             self._box(b"avcC", avcc),
#         )
#
#         stsd = self._full_box(
#             b"stsd",
#             0,
#             0,
#             struct.pack(">I", 1),  # entry_count
#             avc1,
#         )
#         stts = self._full_box(b"stts", 0, 0, struct.pack(">I", 0))
#         stsc = self._full_box(b"stsc", 0, 0, struct.pack(">I", 0))
#         stsz = self._full_box(b"stsz", 0, 0, struct.pack(">I", 0), struct.pack(">I", 0))
#         stco = self._full_box(b"stco", 0, 0, struct.pack(">I", 0))
#         stbl = self._box(b"stbl", stsd, stts, stsc, stsz, stco)
#
#         url_ = self._full_box(b"url ", 0, 1)
#         dref = self._full_box(b"dref", 0, 0, struct.pack(">I", 1), url_)
#         dinf = self._box(b"dinf", dref)
#
#         vmhd = self._full_box(
#             b"vmhd",
#             0,
#             1,
#             struct.pack(">H", 0),
#             struct.pack(">H", 0),
#             struct.pack(">H", 0),
#             struct.pack(">H", 0),
#         )
#
#         mdhd = self._full_box(
#             b"mdhd",
#             0,
#             0,
#             struct.pack(">I", 0),  # creation_time
#             struct.pack(">I", 0),  # modification_time
#             struct.pack(">I", self.timescale),
#             struct.pack(">I", 0),  # duration
#             struct.pack(">H", 0x55C4),  # language = "und"
#             struct.pack(">H", 0),
#         )
#
#         hdlr = self._full_box(
#             b"hdlr",
#             0,
#             0,
#             struct.pack(">I", 0),
#             b"vide",
#             struct.pack(">I", 0),
#             struct.pack(">I", 0),
#             struct.pack(">I", 0),
#             b"VideoHandler\x00",
#         )
#
#         minf = self._box(b"minf", vmhd, dinf, stbl)
#         mdia = self._box(b"mdia", mdhd, hdlr, minf)
#
#         tkhd = self._full_box(
#             b"tkhd",
#             0,
#             7,  # track enabled + in movie + in preview
#             struct.pack(">I", 0),  # creation_time
#             struct.pack(">I", 0),  # modification_time
#             struct.pack(">I", self.track_id),
#             struct.pack(">I", 0),  # reserved
#             struct.pack(">I", 0),  # duration
#             struct.pack(">I", 0),
#             struct.pack(">I", 0),
#             struct.pack(">H", 0),  # layer
#             struct.pack(">H", 0),  # alternate_group
#             struct.pack(">H", 0),  # volume
#             struct.pack(">H", 0),  # reserved
#             self._matrix_bytes(),
#             struct.pack(">I", self.width << 16),
#             struct.pack(">I", self.height << 16),
#         )
#
#         trak = self._box(b"trak", tkhd, mdia)
#
#         mvhd = self._full_box(
#             b"mvhd",
#             0,
#             0,
#             struct.pack(">I", 0),  # creation_time
#             struct.pack(">I", 0),  # modification_time
#             struct.pack(">I", self.timescale),
#             struct.pack(">I", 0),  # duration
#             struct.pack(">I", 0x00010000),  # rate = 1.0
#             struct.pack(">H", 0x0100),  # volume = 1.0
#             struct.pack(">H", 0),
#             struct.pack(">I", 0),
#             struct.pack(">I", 0),
#             self._matrix_bytes(),
#             b"\x00" * 24,  # pre_defined[6]
#             struct.pack(">I", self.track_id + 1),  # next_track_id
#         )
#
#         trex = self._full_box(
#             b"trex",
#             0,
#             0,
#             struct.pack(">I", self.track_id),
#             struct.pack(">I", 1),  # default_sample_description_index
#             struct.pack(">I", self.frame_duration),
#             struct.pack(">I", 0),  # default_sample_size
#             struct.pack(">I", 0),  # default_sample_flags
#         )
#         mvex = self._box(b"mvex", trex)
#
#         moov = self._box(b"moov", mvhd, trak, mvex)
#         return ftyp + moov
#
#     def _build_media_segment(self, sample_data: bytes, pts_us: int, is_key: bool) -> bytes:
#         """
#         Build one movie fragment:
#             moof + mdat
#
#         One sample is packed into one fragment for low-latency streaming.
#         """
#         sample_size = len(sample_data)
#         sample_flags = 0x02000000 if is_key else 0x01010000
#
#         mfhd = self._full_box(
#             b"mfhd",
#             0,
#             0,
#             struct.pack(">I", self.sequence_number),
#         )
#
#         tfhd = self._full_box(
#             b"tfhd",
#             0,
#             0x020000,  # default-base-is-moof
#             struct.pack(">I", self.track_id),
#         )
#
#         tfdt = self._full_box(
#             b"tfdt",
#             1,
#             0,
#             struct.pack(">Q", pts_us),
#         )
#
#         # First pass with placeholder data_offset.
#         trun_placeholder = self._full_box(
#             b"trun",
#             0,
#             0x000001 | 0x000100 | 0x000200 | 0x000400,
#             struct.pack(">I", 1),  # sample_count
#             struct.pack(">i", 0),  # data_offset (patched later)
#             struct.pack(">I", self.frame_duration),
#             struct.pack(">I", sample_size),
#             struct.pack(">I", sample_flags),
#         )
#
#         traf_placeholder = self._box(b"traf", tfhd, tfdt, trun_placeholder)
#         moof_placeholder = self._box(b"moof", mfhd, traf_placeholder)
#
#         # data_offset is from the beginning of moof to the first byte of mdat payload.
#         data_offset = len(moof_placeholder) + 8
#
#         trun = self._full_box(
#             b"trun",
#             0,
#             0x000001 | 0x000100 | 0x000200 | 0x000400,
#             struct.pack(">I", 1),
#             struct.pack(">i", data_offset),
#             struct.pack(">I", self.frame_duration),
#             struct.pack(">I", sample_size),
#             struct.pack(">I", sample_flags),
#         )
#
#         traf = self._box(b"traf", tfhd, tfdt, trun)
#         moof = self._box(b"moof", mfhd, traf)
#         mdat = self._box(b"mdat", sample_data)
#
#         self.sequence_number += 1
#         return moof + mdat
#
#     def _parse_sps_size(self, sps: bytes) -> tuple[int, int]:
#         """
#         Parse coded width/height from SPS.
#
#         This parser is intentionally limited but sufficient for common AVC streams.
#         """
#         sps_body = strip_start_code(sps)
#         if len(sps_body) < 4:
#             raise ValueError("Invalid SPS")
#
#         # Remove NAL header and emulation prevention bytes.
#         rbsp = self._ebsp_to_rbsp(sps_body[1:])
#         br = self._BitReader(rbsp)
#
#         profile_idc = br.read_bits(8)
#         br.read_bits(8)  # constraint flags + reserved bits
#         br.read_bits(8)  # level_idc
#         br.read_ue()  # seq_parameter_set_id
#
#         chroma_format_idc = 1
#         if profile_idc in {
#             100, 110, 122, 244, 44, 83, 86, 118, 128,
#             138, 139, 134, 135
#         }:
#             chroma_format_idc = br.read_ue()
#             if chroma_format_idc == 3:
#                 br.read_bits(1)  # separate_colour_plane_flag
#             br.read_ue()  # bit_depth_luma_minus8
#             br.read_ue()  # bit_depth_chroma_minus8
#             br.read_bits(1)  # qpprime_y_zero_transform_bypass_flag
#             seq_scaling_matrix_present_flag = br.read_bits(1)
#             if seq_scaling_matrix_present_flag:
#                 scaling_count = 8 if chroma_format_idc != 3 else 12
#                 for idx in range(scaling_count):
#                     if br.read_bits(1):
#                         self._skip_scaling_list(br, 16 if idx < 6 else 64)
#
#         br.read_ue()  # log2_max_frame_num_minus4
#         pic_order_cnt_type = br.read_ue()
#         if pic_order_cnt_type == 0:
#             br.read_ue()
#         elif pic_order_cnt_type == 1:
#             br.read_bits(1)
#             br.read_se()
#             br.read_se()
#             num_ref_frames_in_pic_order_cnt_cycle = br.read_ue()
#             for _ in range(num_ref_frames_in_pic_order_cnt_cycle):
#                 br.read_se()
#
#         br.read_ue()  # max_num_ref_frames
#         br.read_bits(1)  # gaps_in_frame_num_value_allowed_flag
#
#         pic_width_in_mbs_minus1 = br.read_ue()
#         pic_height_in_map_units_minus1 = br.read_ue()
#
#         frame_mbs_only_flag = br.read_bits(1)
#         if not frame_mbs_only_flag:
#             br.read_bits(1)  # mb_adaptive_frame_field_flag
#
#         br.read_bits(1)  # direct_8x8_inference_flag
#
#         frame_cropping_flag = br.read_bits(1)
#         frame_crop_left_offset = 0
#         frame_crop_right_offset = 0
#         frame_crop_top_offset = 0
#         frame_crop_bottom_offset = 0
#         if frame_cropping_flag:
#             frame_crop_left_offset = br.read_ue()
#             frame_crop_right_offset = br.read_ue()
#             frame_crop_top_offset = br.read_ue()
#             frame_crop_bottom_offset = br.read_ue()
#
#         width = (pic_width_in_mbs_minus1 + 1) * 16
#         height = (pic_height_in_map_units_minus1 + 1) * 16 * (2 - frame_mbs_only_flag)
#
#         if chroma_format_idc == 0:
#             crop_unit_x = 1
#             crop_unit_y = 2 - frame_mbs_only_flag
#         elif chroma_format_idc == 1:
#             crop_unit_x = 2
#             crop_unit_y = 2 * (2 - frame_mbs_only_flag)
#         elif chroma_format_idc == 2:
#             crop_unit_x = 2
#             crop_unit_y = 1 * (2 - frame_mbs_only_flag)
#         else:
#             crop_unit_x = 1
#             crop_unit_y = 1 * (2 - frame_mbs_only_flag)
#
#         width -= (frame_crop_left_offset + frame_crop_right_offset) * crop_unit_x
#         height -= (frame_crop_top_offset + frame_crop_bottom_offset) * crop_unit_y
#
#         return max(width, 16), max(height, 16)
#
#     def _skip_scaling_list(self, br: "_BitReader", size_of_scaling_list: int) -> None:
#         """Skip one SPS scaling list."""
#         last_scale = 8
#         next_scale = 8
#         for _ in range(size_of_scaling_list):
#             if next_scale != 0:
#                 delta_scale = br.read_se()
#                 next_scale = (last_scale + delta_scale + 256) % 256
#             last_scale = next_scale if next_scale != 0 else last_scale
#
#     def _ebsp_to_rbsp(self, data: bytes) -> bytes:
#         """Remove emulation prevention bytes (0x03) from EBSP."""
#         out = bytearray()
#         zero_count = 0
#         for b in data:
#             if zero_count == 2 and b == 0x03:
#                 zero_count = 0
#                 continue
#             out.append(b)
#             if b == 0:
#                 zero_count += 1
#             else:
#                 zero_count = 0
#         return bytes(out)
#
#     def _matrix_bytes(self) -> bytes:
#         """Return the standard unity transformation matrix."""
#         return b"".join([
#             struct.pack(">I", 0x00010000),  # a
#             struct.pack(">I", 0x00000000),  # b
#             struct.pack(">I", 0x00000000),  # u
#             struct.pack(">I", 0x00000000),  # c
#             struct.pack(">I", 0x00010000),  # d
#             struct.pack(">I", 0x00000000),  # v
#             struct.pack(">I", 0x00000000),  # x
#             struct.pack(">I", 0x00000000),  # y
#             struct.pack(">I", 0x40000000),  # w
#         ])
#
#     def _box(self, box_type: bytes, *payloads: bytes) -> bytes:
#         """Build a generic ISO BMFF box."""
#         payload = b"".join(payloads)
#         return struct.pack(">I4s", 8 + len(payload), box_type) + payload
#
#     def _full_box(self, box_type: bytes, version: int, flags: int, *payloads: bytes) -> bytes:
#         """Build a full box with version and flags."""
#         payload = bytes([version]) + flags.to_bytes(3, "big") + b"".join(payloads)
#         return self._box(box_type, payload)



import io
import struct
from fractions import Fraction
from typing import Iterator, List, Optional

import av
from av.codec import CodecContext

START_CODE_3 = b"\x00\x00\x01"
START_CODE_4 = b"\x00\x00\x00\x01"


def find_nal_units_annexb(data: bytes) -> List[bytes]:
    """
    Split one Annex-B byte buffer into NAL units while preserving start codes.

    This helper is intentionally lightweight:
    - it is only used on already packetized / parser-produced chunks
    - it does not try to repair cross-buffer truncation
    """
    positions: List[int] = []
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

    out: List[bytes] = []
    for idx, start in enumerate(positions):
        end = positions[idx + 1] if idx + 1 < len(positions) else len(data)
        out.append(data[start:end])
    return out


def strip_start_code(nal: bytes) -> bytes:
    """
    Remove one Annex-B start code prefix if present.
    """
    if nal.startswith(START_CODE_4):
        return nal[4:]
    if nal.startswith(START_CODE_3):
        return nal[3:]
    return nal


def nal_type(nal: bytes) -> int:
    """
    Return H.264 NAL unit type for one Annex-B NAL.
    """
    body = strip_start_code(nal)
    if not body:
        return -1
    return body[0] & 0x1F


def is_vcl_nal(nal_type_value: int) -> bool:
    """
    H.264 VCL slice types used here:
    - 1: non-IDR slice
    - 5: IDR slice
    """
    return nal_type_value in (1, 5)


def contains_idr(frame_annexb: bytes) -> bool:
    """
    Whether an Annex-B access unit contains an IDR NAL.
    """
    for nal in find_nal_units_annexb(frame_annexb):
        if nal_type(nal) == 5:
            return True
    return False


def _has_sps(frame_annexb: bytes) -> bool:
    for nal in find_nal_units_annexb(frame_annexb):
        if nal_type(nal) == 7:
            return True
    return False


def _has_pps(frame_annexb: bytes) -> bool:
    for nal in find_nal_units_annexb(frame_annexb):
        if nal_type(nal) == 8:
            return True
    return False


def _has_any_vcl(frame_annexb: bytes) -> bool:
    for nal in find_nal_units_annexb(frame_annexb):
        if is_vcl_nal(nal_type(nal)):
            return True
    return False


def _annexb_frame_to_avcc_sample(frame_annexb: bytes) -> bytes:
    """
    Convert one Annex-B access unit into one MP4-compatible H.264 sample payload.

    Output layout:
        [len][nal][len][nal]...

    SPS / PPS / AUD are not included in the media sample because the MP4 init
    segment should already carry decoder configuration (avcC / extradata).
    SEI is preserved.
    """
    out = bytearray()

    for nal in find_nal_units_annexb(frame_annexb):
        t = nal_type(nal)
        if t in (7, 8, 9):  # SPS / PPS / AUD
            continue

        body = strip_start_code(nal)
        if not body:
            continue

        out.extend(struct.pack(">I", len(body)))
        out.extend(body)

    return bytes(out)


class H264AnnexBFramer:
    """
    Reframe a continuous H.264 Annex-B byte stream into access-unit-like chunks.

    External contract is intentionally kept unchanged:
    - constructor signature stays the same
    - decode(chunk) still yields:
          [is_key: 1 byte][pts_us: 8 bytes][Annex-B access unit bytes]

    Internal strategy:
    - PyAV parser is responsible for raw H.264 packet boundary detection
    - this class still keeps a small amount of transport-oriented logic:
      * cache SPS/PPS
      * group non-VCL prefix NALs with the next VCL access unit
      * optionally prepend latest SPS/PPS before IDR output
    """

    def __init__(self, max_fps: int):
        self.parser = CodecContext.create("h264", "r")

        self.last_sps: Optional[bytes] = None
        self.last_pps: Optional[bytes] = None

        self.pending_prefix: List[bytes] = []

        self.frame_interval_us = int(1_000_000 / max(max_fps, 1))
        self._pts_us = 0

    def construct_return_val(self, frame_annexb: bytes) -> bytes:
        """
        Build the existing transport packet:
            [is_key:1][pts_us:8][frame_annexb]
        """
        is_key = 1 if contains_idr(frame_annexb) else 0
        header = struct.pack(">BQ", is_key, self._pts_us)
        self._pts_us += self.frame_interval_us
        return header + frame_annexb

    def _remember_parameter_sets(self, frame_annexb: bytes) -> None:
        """
        Update cached SPS/PPS from one Annex-B chunk.
        """
        for nal in find_nal_units_annexb(frame_annexb):
            t = nal_type(nal)
            if t == 7:
                self.last_sps = nal
            elif t == 8:
                self.last_pps = nal

    def _finalize_access_unit(self, frame_annexb: bytes) -> bytes:
        """
        Normalize one output access unit.

        For IDR output, prepend the latest cached SPS/PPS when they are not
        already present in the current frame. This keeps browser-side recovery
        behaviour close to the original implementation.
        """
        self._remember_parameter_sets(frame_annexb)

        if contains_idr(frame_annexb):
            prefix = bytearray()
            if self.last_sps is not None and not _has_sps(frame_annexb):
                prefix.extend(self.last_sps)
            if self.last_pps is not None and not _has_pps(frame_annexb):
                prefix.extend(self.last_pps)
            if prefix:
                return bytes(prefix) + frame_annexb

        return frame_annexb

    def decode(self, chunk: bytes) -> Iterator[bytes]:
        """
        Feed raw H.264 Annex-B bytes and yield wrapped access units.

        PyAV parser performs the low-level splitting. This method then restores
        the previous framing semantics by collecting parameter/AUD/SEI prefix
        data until a VCL packet is seen.
        """
        for packet in self.parser.parse(chunk):
            raw = bytes(packet)
            if not raw:
                continue

            self._remember_parameter_sets(raw)

            if _has_any_vcl(raw):
                # frame_annexb = b"".join(self.pending_prefix) + raw
                # self.pending_prefix.clear()
                frame_annexb = raw

                frame_annexb = self._finalize_access_unit(frame_annexb)
                yield self.construct_return_val(frame_annexb)
            else:
                self.pending_prefix.append(raw)

    def flush(self) -> Optional[bytes]:
        """
        Flush parser tail and pending prefix data.

        The original method returned raw Annex-B bytes (not the wrapped transport
        packet), so that behaviour is preserved.
        """
        flushed_parts: List[bytes] = []

        for packet in self.parser.parse(b""):
            raw = bytes(packet)
            if raw:
                flushed_parts.append(raw)

        if self.pending_prefix:
            flushed_parts = self.pending_prefix + flushed_parts
            self.pending_prefix.clear()

        if not flushed_parts:
            return None

        frame_annexb = b"".join(flushed_parts)
        return self._finalize_access_unit(frame_annexb)


class H264FMP4Framer:
    """
    Convert a continuous Annex-B H.264 stream into fragmented MP4 packets.

    External contract is intentionally unchanged:
    - constructor signature stays the same
    - decode(chunk) still yields:
          [is_key: 1 byte][pts_us: 8 bytes][fMP4 bytes]

    Design:
    - PyAV parser is used to split the raw Annex-B stream
    - PyAV muxer is used to generate the MP4 init segment and media fragments
    - a minimal amount of manual logic remains for:
      * SPS/PPS tracking
      * IDR-aligned muxer reinitialization when stream config changes
      * Annex-B -> AVCC sample conversion for one MP4 media sample
    """

    def __init__(self, max_fps: int):
        self.parser = av.CodecContext.create("h264", "r")

        self.pending_prefix: List[bytes] = []

        self.last_sps: Optional[bytes] = None
        self.last_pps: Optional[bytes] = None

        self.init_sps: Optional[bytes] = None
        self.init_pps: Optional[bytes] = None

        self.timescale = 1_000_000
        self.frame_duration = int(1_000_000 / max(max_fps, 1))
        self._pts_us = 0

        self._mux_buffer: Optional[io.BytesIO] = None
        self._mux_read_pos = 0
        self._mux_container = None
        self._mux_stream = None

    def _wrap_packet(self, is_key: bool, pts_us: int, payload: bytes) -> bytes:
        """
        Keep the original transport packet format.
        """
        header = struct.pack(">BQ", 1 if is_key else 0, pts_us)
        return header + payload

    def _remember_parameter_sets(self, frame_annexb: bytes) -> None:
        """
        Update cached SPS/PPS from one Annex-B access unit.
        """
        for nal in find_nal_units_annexb(frame_annexb):
            t = nal_type(nal)
            if t == 7:
                self.last_sps = nal
            elif t == 8:
                self.last_pps = nal

    def _with_parameter_sets_for_probe(self, frame_annexb: bytes) -> bytes:
        """
        Ensure the probe sample contains SPS/PPS before a keyframe, so that the
        temporary raw-H264 input container has enough codec configuration to
        produce a correct output stream template.
        """
        self._remember_parameter_sets(frame_annexb)

        if not contains_idr(frame_annexb):
            return frame_annexb

        prefix = bytearray()
        if self.last_sps is not None and not _has_sps(frame_annexb):
            prefix.extend(self.last_sps)
        if self.last_pps is not None and not _has_pps(frame_annexb):
            prefix.extend(self.last_pps)

        return bytes(prefix) + frame_annexb if prefix else frame_annexb

    def _drain_mux_buffer(self) -> bytes:
        """
        Read only the newly appended bytes from the output buffer.
        """
        if self._mux_buffer is None:
            return b""

        current = self._mux_buffer.getvalue()
        if self._mux_read_pos >= len(current):
            return b""

        out = current[self._mux_read_pos:]
        self._mux_read_pos = len(current)
        return out

    def _close_muxer(self) -> None:
        """
        Close the current muxer instance if present.

        Any trailer bytes produced during close are intentionally discarded,
        because this class is used for live fragmented streaming, not for
        finalized MP4 file writing.
        """
        if self._mux_container is not None:
            try:
                self._mux_container.close()
            except Exception:
                pass

        self._mux_container = None
        self._mux_stream = None
        self._mux_buffer = None
        self._mux_read_pos = 0

    def _reset_muxer(self, probe_annexb: bytes) -> bytes:
        """
        Recreate the fragmented MP4 muxer from a raw H.264 probe sample.

        The new output stream is created from a temporary raw-H264 input stream
        template. This is the most reliable PyAV-level remux setup for preserving
        codec parameters without transcoding.
        """
        self._close_muxer()

        probe_buffer = io.BytesIO(probe_annexb)
        probe_input = av.open(probe_buffer, mode="r", format="h264")

        try:
            in_stream = probe_input.streams.video[0]

            self._mux_buffer = io.BytesIO()
            self._mux_read_pos = 0

            self._mux_container = av.open(
                self._mux_buffer,
                mode="w",
                format="mp4",
                options={
                    "movflags": "empty_moov+frag_every_frame+default_base_moof",
                    "flush_packets": "1",
                },
            )

            self._mux_stream = self._mux_container.add_stream(template=in_stream)

            # Use the existing transport timestamp unit directly: microseconds.
            # Keeping packet time_base explicit avoids implicit rescaling surprises.
            self._mux_stream.time_base = Fraction(1, self.timescale)
            try:
                self._mux_stream.codec_context.time_base = Fraction(1, self.timescale)
            except Exception:
                # Some builds may not allow touching codec_context.time_base here.
                pass

            self._mux_container.start_encoding()
            return self._drain_mux_buffer()

        finally:
            probe_input.close()

    def decode(self, chunk: bytes) -> Iterator[bytes]:
        """
        Feed raw H.264 Annex-B bytes and emit one or more transport packets.

        Emission policy:
        - a new init segment is emitted when muxer is first created
        - if SPS/PPS changes, a fresh init segment is emitted on the next IDR
        - each completed access unit yields one media fragment packet
        """
        for parsed_packet in self.parser.parse(chunk):
            raw = bytes(parsed_packet)
            if not raw:
                continue

            self._remember_parameter_sets(raw)

            if _has_any_vcl(raw):
                frame_annexb = b"".join(self.pending_prefix) + raw
                self.pending_prefix.clear()
            else:
                self.pending_prefix.append(raw)
                continue

            frame_annexb = self._with_parameter_sets_for_probe(frame_annexb)
            has_idr = contains_idr(frame_annexb)

            pts_us = self._pts_us
            self._pts_us += self.frame_duration

            # We cannot initialize an MP4 stream correctly without SPS/PPS.
            if self.last_sps is None or self.last_pps is None:
                continue

            need_new_init = (
                self._mux_container is None
                or (
                    has_idr
                    and (
                        self.init_sps != self.last_sps
                        or self.init_pps != self.last_pps
                    )
                )
            )

            if need_new_init:
                # Reinitialize only at a clean keyframe boundary.
                if not has_idr:
                    continue

                init_segment = self._reset_muxer(frame_annexb)
                self.init_sps = self.last_sps
                self.init_pps = self.last_pps

                if init_segment:
                    yield self._wrap_packet(True, pts_us, init_segment)

            if self._mux_container is None or self._mux_stream is None:
                continue

            sample_payload = _annexb_frame_to_avcc_sample(frame_annexb)
            if not sample_payload:
                continue

            pkt = av.Packet(sample_payload)
            pkt.stream = self._mux_stream
            pkt.pts = pts_us
            pkt.dts = pts_us
            pkt.duration = self.frame_duration
            pkt.time_base = Fraction(1, self.timescale)

            self._mux_container.mux_one(pkt)

            media_segment = self._drain_mux_buffer()
            if media_segment:
                yield self._wrap_packet(has_idr, pts_us, media_segment)

    def close(self) -> None:
        """
        Explicit resource cleanup for the internal muxer.

        Optional to call in your current flow, but harmless and useful if you
        later add an explicit shutdown hook.
        """
        self._close_muxer()
