# Agent Configuration

mode: chat
scope: per-sender
activation: always

## Embedded Agents

### draftsman
- **Когда вызывать:** Когда нужно что-то нарисовать или оформить в AutoCAD (план, чертёж, схема, DWG, PDF).
- **Как вызывать:** Embedded вызов агента `draftsman`.
- **Что передавать:** ТЗ строго по 4 пунктам (ЦЕЛЬ, ВХОДНЫЕ ДАННЫЕ, СРОК, ФОРМАТ).
- **Что получаешь:** Готовый DWG + PDF с отчётом о самопроверке.
