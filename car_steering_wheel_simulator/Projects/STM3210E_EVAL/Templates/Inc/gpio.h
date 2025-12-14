#ifndef __GPIO_H
#define __GPIO_H

#include "main.h"

#define LED1(X) HAL_GPIO_WritePin(LED1_GPIO_PORT, LED1_PIN, X)
#define LED2(X) HAL_GPIO_WritePin(LED2_GPIO_PORT, LED2_PIN, X)
#define LED3(X) HAL_GPIO_WritePin(LED3_GPIO_PORT, LED3_PIN, X)
#define LED4(X) HAL_GPIO_WritePin(LED4_GPIO_PORT, LED4_PIN, X)

#define WAKE_UP HAL_GPIO_ReadPin(WAKEUP_BUTTON_GPIO_PORT, WAKEUP_BUTTON_PIN) 
#define TAMPER  HAL_GPIO_ReadPin(TAMPER_BUTTON_GPIO_PORT, TAMPER_BUTTON_PIN) 

#define LEFT_TRIG   HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12)
#define RIGHT_TRIG  HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_13)
#define LEFT_BTN    HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_14)
#define RIGHT_BTN   HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_15)

#define ENC_A       HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_2)
#define ENC_B       HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_7)
#define ENC_I       HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_6)

void HAL_USER_GPIO_Init(void);
int16_t HAL_USER_GetEncoderValue(void);
int16_t HAL_USER_GetEncoderIndex(void);
#endif /* __GPIO_H */