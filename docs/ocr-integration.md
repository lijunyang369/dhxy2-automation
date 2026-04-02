# OCR 鎺ュ叆鏂规

## 1. 鐩爣

`dhxy2-automation` 涓嶇洿鎺ュ畨瑁呭拰寮曠敤 PaddleOCR銆? 
椤圭洰閫氳繃鏈満 OCR 服务 鏈嶅姟鑾峰彇 OCR 鑳藉姏銆?
杩欐牱鍋氱殑鐩爣鏄細

- 閬垮厤涓婚」鐩幆澧冨啿绐?- 闄嶄綆椤圭洰渚濊禆澶嶆潅搴?- 淇濇寔妯″潡杈圭晫娓呮櫚
- 渚夸簬鍚庣画鏇挎崲 OCR 瀹炵幇

## 2. 鎺ュ叆鍘熷垯

鏈」鐩腑锛?
- `perception` 璐熻矗鈥滀綍鏃堕渶瑕?OCR鈥?- `OCRClient` 璐熻矗鈥滃浣曡姹?OCR 鏈嶅姟鈥?- OCR 服务 璐熻矗鈥滃浣曡繍琛?PaddleOCR鈥?
绂佹锛?
- 鍦ㄤ笟鍔℃ā鍧楃洿鎺?import PaddleOCR
- 鍦ㄧ瓥鐣ュ眰鐩存帴鍙?HTTP 璇锋眰
- 鍦ㄧ姸鎬佹満灞傜洿鎺ヨВ鏋愬師濮?OCR provider 鍝嶅簲

## 3. 鎺ㄨ崘妯″潡浣嶇疆

寤鸿鏂板妯″潡锛?
- `src/perception/ocr_client.py`
- `src/perception/ocr_models.py`
- `src/perception/ocr_profiles.py`

鑱岃矗寤鸿锛?
### `ocr_client.py`

- 灏佽 HTTP 璇锋眰
- 澶勭悊瓒呮椂銆佽繛鎺ュけ璐ャ€佸搷搴旇В鏋?
### `ocr_models.py`

- 瀹氫箟 `OCRTextResult`
- 瀹氫箟 `OCRLineResult`
- 瀹氫箟 `OCRErrorResult`

### `ocr_profiles.py`

- 瀹氫箟椤圭洰鍐?profile 鍚嶇О
- 绾︽潫鍝簺鍖哄煙璧板摢浜?OCR 鍙傛暟

## 4. 閰嶇疆寤鸿

寤鸿鍦ㄧ幆澧冮厤缃噷澧炲姞锛?
```json
{
  "ocr_service": {
    "enabled": true,
    "base_url": "http://127.0.0.1:18080",
    "timeout_ms": 1500
  }
}
```

绾︽潫锛?
- `enabled=false` 鏃堕」鐩繀椤诲彲浠ラ檷绾ц繍琛?- `base_url` 蹇呴』鏄湰鏈哄湴鍧€

## 5. 鎺ㄨ崘璋冪敤鏂瑰紡

瀵?`perception` 灞傚彧鏆撮湶缁熶竴鎺ュ彛锛?
```python
client.read_text(image_path, profile="battle_tip")
client.read_lines(image_path, profile="round_text")
```

涓嶈鎶?HTTP 缁嗚妭鎵╂暎鍒颁笟鍔′唬鐮併€?
## 6. 涓庡綋鍓嶅洖鍚堣瘑鍒殑鍏崇郴

褰撳墠鍥炲悎璇嗗埆涓嶅缓璁珛鍒诲畬鍏ㄤ緷璧?OCR 服务銆? 
鏇村悎鐞嗙殑鏂瑰紡鏄細

- 涓撶敤鏁板瓧璇嗗埆浠嶇劧淇濈暀
- OCR 服务 浣滀负杈呰矾寰勬垨鍚庡璺緞

閫傚悎鐢?OCR 服务 鐨勫尯鍩燂細

- 鎻愮ず鏂囨湰
- 鐘舵€佹枃妗?- 鎸夐挳鏂囧瓧
- 缁撶畻鏂囧瓧

鍥炲悎璇嗗埆寤鸿锛?
- 涓€鏈熺户缁互涓撶敤鏁板瓧璇嗗埆涓轰富
- 浜屾湡鍐嶆帴鍏?OCR 服务 浣滀负杈呭姪鏍￠獙

## 7. 閿欒澶勭悊瑕佹眰

OCR 服务 璋冪敤澶辫触鏃讹細

- 涓嶈兘璁╂暣涓嚜鍔ㄥ寲涓诲惊鐜洿鎺ュ穿婧?- 蹇呴』杩斿洖缁撴瀯鍖栧け璐ョ粨鏋?- 蹇呴』甯﹀け璐ュ師鍥犲拰鑰楁椂

寤鸿閿欒绫诲瀷锛?
- `service_unavailable`
- `request_timeout`
- `invalid_response`
- `ocr_failed`

## 8. 娴嬭瘯瑕佹眰

椤圭洰鍐呮祴璇曚笉搴斾緷璧栫湡瀹?OCR 服务 甯搁┗杩愯銆? 
寤鸿鍒嗗眰锛?
### 鍗曞厓娴嬭瘯

- mock `OCRClient`
- 楠岃瘉 perception 妯″潡濡備綍瑙ｉ噴 OCR 缁撴灉

### 闆嗘垚娴嬭瘯

- 浠呭湪闇€瑕佹椂楠岃瘉 sidecar 鎺ュ彛鑱旈€?
### Smoke

- 榛樿涓嶈姹傛湰鏈哄繀椤诲厛鍚姩 OCR 服务
- 瀵?sidecar 鐨勪緷璧栧簲鍙垏鎹负 mock 鎴栧叧闂?
## 9. 瀹炴柦寤鸿

### Phase 1

- 鎶借薄 `OCRClient`
- 澧炲姞鐜閰嶇疆
- 鍏堜笉鎺ョ湡瀹?sidecar锛屽彧鎶婅竟鐣屾惌濂?
### Phase 2

- 鎺ラ€氭湰鏈?OCR 服务
- 鍦ㄥ皯閲忓尯鍩熷惎鐢ㄧ湡瀹?OCR

### Phase 3

- 鏍规嵁鏁堟灉鍐冲畾鏄惁鎵╁ぇ鎺ュ叆闈?
## 10. 鏈€缁堣姹?
鏈」鐩悗缁秹鍙?OCR 鐨勫姛鑳介粯璁ゆ寜浠ヤ笅瑙勫垯瀹炵幇锛?
1. 椤圭洰涓嶇洿鎺ヤ緷璧?PaddleOCR
2. OCR 閫氳繃 sidecar 鏈嶅姟璁块棶
3. OCR 璋冪敤杈圭晫鍙嚭鐜板湪 `perception` 灞?4. 鐘舵€佹満鍜岀瓥鐣ュ眰鍙秷璐圭粨鏋勫寲 OCR 缁撴灉

