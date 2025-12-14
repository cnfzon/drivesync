#ifndef __LCD_H
#define __LCD_H

#include "stm32f1xx_hal.h"

#define Reset_LCD         0xe2

#define Set_Start_Line_X  0x40
#define Set_Page_Addr_X   0xb0
#define Set_ColH_Addr_X   0x10
#define Set_ColL_Addr_X   0x0

#define LCD_Reset   0xe2
#define Display_Off   0xae
#define Display_On    0xaf
#define Set_ADC_Normal    0xa0
#define Set_ADC_Reverse   0xa1
#define Set_LCD_Bias_7    0xa3
#define Set_LCD_Bias_9    0xa2
#define RMW_Mode_En       0xe0
#define RMW_Mode_Dis      0xee
#define COM_Scan_Dir_Normal 0xc0
#define COM_Scan_Dir_Reverse  0xc8

#define Set_Resistor_Ratio_X   0x20
#define Set_Ref_Vol_Mode       0x81
#define Set_Ref_Vol_Reg        0x20

#define Display_Normal    0xa6
#define Display_Reverse   0xa7
#define Display_All_On    0xa5
#define Display_All_Normal  0xa4
// ZYMG12864
/*A0=0  -- cmd*/
#define LCD_Command  *((volatile unsigned char * )0x6c000000)
/*A0=1 -- data*/
#define LCD_Data  *((volatile unsigned char * )0x6c000001)

/*define the constant for display digital char*/
#define	D0		0
#define	D1		1
#define	D2		2
#define	D3		3
#define	D4		4
#define	D5		5
#define	D6		6
#define	D7		7
#define	D8		8
#define	D9		9
#define	DPoint	10	//"."
#define DDash	20	//"-"
#define DColon	21	//":"

#define Da	30
#define Db	31
#define Dc	32
#define Dd	33

#define De	34
#define Df	35
#define Dg	36
#define Dh	37
#define Di	38
#define Dj	39
#define Dk	40
#define Dl	41
#define Dm	42
#define Dn	43
#define Do	44
#define Dp	45
#define Dq	46
#define Dr	47
#define Ds	48
#define Dt	49
#define Du	50

#define Dv	51
#define Dw	52
#define Dx	53
#define Dy	54
#define Dz	55

#define DA	56
#define DB	57
#define DC	58
#define DD	59
#define DE	60
#define DF	61
#define DG	62
#define DH	63
#define DI	64
#define DJ	65
#define DK	66
#define DL	67
#define DM	68
#define DN	69
#define DO	70
#define DP	71
#define DQ	72
#define DR	73
#define DS	74
#define DT	75
#define DU	76
#define DV	77
#define DW	78
#define DX	79
#define DY	80
#define DZ	81

extern unsigned char DispSTLoGoTable[];
extern unsigned char ChineseTable[][16];

unsigned char LCD_DrawString(unsigned char Xpos, unsigned char Ypos, unsigned char *c, unsigned char length);
void LCD_Init(void);
void STM3210E_LCD_Init(void);
void Converse_Logo(void);
void LCD_Clear(void);

void LCD_DrawChar(unsigned char Xpos, unsigned char Ypos, unsigned char offset);

void LCD_PowerOn(void);
void LCD_DisplayOn(void);
void LCD_DisplayOff(void);

void LCD_CtrlLinesConfig(void);
void LCD_FSMCConfig(void);

void delay(void);
void reset_delay(void);
void power_delay(void);

void LCD_Draw_ST_Logo(void);
void LCD_Reset_Cursor(void);
void LCD_Clr_Cursor(signed char x);
void LCD_Set_Cursor(signed char x);

unsigned char Get_Index_From_ASCII(char c);
void LCD_DrawString_Text(unsigned char Xpage, unsigned char YCol, char *str);
#endif /* __LCD_H */
