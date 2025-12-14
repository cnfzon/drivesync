#ifndef __RTC_H
#define __RTC_H

#include "main.h"

extern RTC_HandleTypeDef hrtc;

// #define RTC_CLOCK_SOURCE_LSE
#define RTC_CLOCK_SOURCE_LSI  

void HAL_USER_RTC_Init(void);
void HAL_USER_RTC_GetTime(uint8_t *hour, uint8_t *min, uint8_t *sec);
void HAL_USER_RTC_GetDate(uint8_t *year, uint8_t *month, uint8_t *date, uint8_t *weekDay);
void HAL_USER_RTC_SetTimeDate(uint8_t year, uint8_t month, uint8_t date, uint8_t weekDay, uint8_t hour, uint8_t min, uint8_t sec);

#endif /* __RTC_H */