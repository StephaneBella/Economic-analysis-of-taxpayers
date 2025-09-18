* Encoding: UTF-8.

DATASET ACTIVATE Jeu_de_données2.
RECODE Delta19 (1=2) (-1=0) (0=1) INTO Confmp19.
VARIABLE LABELS  Confmp19 'Confirmité de déclaration marché en 2019'.
EXECUTE.

DATASET ACTIVATE Jeu_de_données2.
RECODE Delta20 (1=2) (-1=0) (0=1) INTO Confmp20.
VARIABLE LABELS  Confmp20 'Confirmité de déclaration marché en 2020'.
EXECUTE.

DATASET ACTIVATE Jeu_de_données2.
RECODE Delta21 (1=2) (-1=0) (0=1) INTO Confmp21.
VARIABLE LABELS  Confmp21 'Confirmité de déclaration marché en 2021'.
EXECUTE.

DATASET ACTIVATE Jeu_de_données2.
RECODE Delta22 (1=2) (-1=0) (0=1) INTO Confmp22.
VARIABLE LABELS  Confmp22 'Confirmité de déclaration marché en 2022'.
EXECUTE.


DATASET ACTIVATE Jeu_de_données2.
RECODE Delta23 (1=2) (-1=0) (0=1) INTO Confmp23.
VARIABLE LABELS  Confmp23 'Confirmité de déclaration marché en 2023'.
EXECUTE.

DATASET ACTIVATE Jeu_de_données2.
RECODE Delta24 (1=2) (-1=0) (0=1) INTO Confmp24.
VARIABLE LABELS  Confmp24 'Confirmité de déclaration marché en 2024'.
EXECUTE.
/*=====================================================================================*/
RECODE Classetax24 (Lowest thru 99999=1) (ELSE=2) INTO gctax.
VARIABLE LABELS  gctax 'groupe de compte de gestion des contribuable'.
EXECUTE.
/*=====================================================================================*/
RECODE TxdDSFMp (1=0) (0=2) (0.0001 thru 0.99=1) INTO Tdecmp.
VARIABLE LABELS  Tdecmp 'Type de déclarant des marchés publics dans les DSF'.
EXECUTE.
 /* =====================================================================================*/
RECODE Ecart19 (0 thru Highest=0) (ELSE=1) INTO MinCA19.
VARIABLE LABELS  MinCA19 "Minoration du chiffre d'affaires en 2019".
EXECUTE.

RECODE Ecart20 (0 thru Highest=0) (ELSE=1) INTO MinCA20.
VARIABLE LABELS  MinCA20 "Minoration du chiffre d'affaires en 2020".
EXECUTE.

RECODE Ecart21 (0 thru Highest=0) (ELSE=1) INTO MinCA21.
VARIABLE LABELS  MinCA21 "Minoration du chiffre d'affaires en 2021".
EXECUTE.

RECODE Ecart22 (0 thru Highest=0) (ELSE=1) INTO MinCA22.
VARIABLE LABELS  MinCA22 "Minoration du chiffre d'affaires en 2022".
EXECUTE.

RECODE Ecart23 (0 thru Highest=0) (ELSE=1) INTO MinCA23.
VARIABLE LABELS  MinCA23 "Minoration du chiffre d'affaires en 2023".
EXECUTE.

RECODE Ecart24 (0 thru Highest=0) (ELSE=1) INTO MinCA24.
VARIABLE LABELS  MinCA24 "Minoration du chiffre d'affaires en 2024".
EXECUTE.
