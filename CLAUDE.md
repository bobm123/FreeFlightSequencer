# Claude Code Generation Context

This file contains important guidelines and constraints for AI-assisted code generation in this Arduino project.

## Code Generation Guidelines

### Serial Output Character Set
**IMPORTANT**: Avoid using special Unicode characters in Serial.print() and Serial.println() statements.

**Rationale**: While the Arduino IDE supports Unicode characters, future display devices (LCD displays, terminal emulators, embedded displays, etc.) may have limited character sets that cannot render special characters properly.

**Examples:**
```cpp
// ❌ AVOID - Special Unicode characters
Serial.println("✅ Test passed");
Serial.println("❌ Test failed"); 
Serial.println("🔧 Debug info");
Serial.println("⚠️ Warning");

// ✅ PREFERRED - Standard ASCII characters
Serial.println("[OK] Test passed");
Serial.println("[FAIL] Test failed");
Serial.println("[DEBUG] Debug info"); 
Serial.println("[WARN] Warning");
```

**Alternative Approaches:**
- Use standard ASCII brackets: `[OK]`, `[FAIL]`, `[WARN]`, `[INFO]`, `[DEBUG]`
- Use text indicators: `PASS`, `FAIL`, `ERROR`, `WARNING`, `INFO`
- Use simple symbols: `+`, `-`, `!`, `*`, `>`

### Additional Guidelines

#### Memory Efficiency
- Prefer `F()` macro for string literals to store them in Flash memory
- Example: `Serial.println(F("System initialized"));`

#### Consistent Formatting
- Use consistent prefixes for log levels
- Include timestamps when appropriate
- Keep messages concise but informative

#### Example Serial Output Format
```cpp
// Consistent logging format
Serial.println(F("[INIT] Hardware initialization starting..."));
Serial.println(F("[OK] Button HAL initialized"));
Serial.println(F("[OK] NeoPixel HAL initialized"));
Serial.println(F("[WARN] GPS not detected, continuing without GPS"));
Serial.println(F("[INFO] System ready"));
```

This ensures maximum compatibility across different display devices and maintains professional, readable output formatting.