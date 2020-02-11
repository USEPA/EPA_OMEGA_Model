import numpy as np
import unit_conversions as convert
import matplotlib.pyplot as plt

ftp_phase1_time = np.array((
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
    49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
    72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94,
    95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131,
    132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149,
    150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167,
    168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185,
    186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203,
    204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221,
    222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239,
    240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257,
    258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275,
    276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293,
    294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311,
    312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
    330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347,
    348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365,
    366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383,
    384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401,
    402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419,
    420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437,
    438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455,
    456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473,
    474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491,
    492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505))

ftp_phase1_speed_mph = np.array((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 5.9, 8.6, 11.5, 14.3,
                                 16.9, 17.3, 18.1, 20.7, 21.7, 22.4, 22.5, 22.1, 21.5, 20.9, 20.4, 19.8, 17, 14.9, 14.9,
                                 15.2, 15.5, 16, 17.1, 19.1, 21.1, 22.7, 22.9, 22.7, 22.6, 21.3, 19, 17.1, 15.8, 15.8,
                                 17.7, 19.8, 21.6, 23.2, 24.2, 24.6, 24.9, 25, 24.6, 24.5, 24.7, 24.8, 24.7, 24.6, 24.6,
                                 25.1, 25.6, 25.7, 25.4, 24.9, 25, 25.4, 26, 26, 25.7, 26.1, 26.7, 27.5, 28.6, 29.3,
                                 29.8, 30.1, 30.4, 30.7, 30.7, 30.5, 30.4, 30.3, 30.4, 30.8, 30.4, 29.9, 29.5, 29.8,
                                 30.3, 30.7, 30.9, 31, 30.9, 30.4, 29.8, 29.9, 30.2, 30.7, 31.2, 31.8, 32.2, 32.4, 32.2,
                                 31.7, 28.6, 25.3, 22, 18.7, 15.4, 12.1, 8.8, 5.5, 2.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 3.3, 6.6, 9.9, 13.2, 16.5, 19.8, 22.2, 24.3, 25.8, 26.4, 25.7, 25.1, 24.7, 25, 25.2,
                                 25.4, 25.8, 27.2, 26.5, 24, 22.7, 19.4, 17.7, 17.2, 18.1, 18.6, 20, 22.2, 24.5, 27.3,
                                 30.5, 33.5, 36.2, 37.3, 39.3, 40.5, 42.1, 43.5, 45.1, 46, 46.8, 47.5, 47.5, 47.3, 47.2,
                                 47, 47, 47, 47, 47, 47.2, 47.4, 47.9, 48.5, 49.1, 49.5, 50, 50.6, 51, 51.5, 52.2, 53.2,
                                 54.1, 54.6, 54.9, 55, 54.9, 54.6, 54.6, 54.8, 55.1, 55.5, 55.7, 56.1, 56.3, 56.6, 56.7,
                                 56.7, 56.5, 56.5, 56.5, 56.5, 56.5, 56.5, 56.4, 56.1, 55.8, 55.1, 54.6, 54.2, 54, 53.7,
                                 53.6, 53.9, 54, 54.1, 54.1, 53.8, 53.4, 53, 52.6, 52.1, 52.4, 52, 51.9, 51.7, 51.5,
                                 51.6, 51.8, 52.1, 52.5, 53, 53.5, 54, 54.9, 55.4, 55.6, 56, 56, 55.8, 55.2, 54.5, 53.6,
                                 52.5, 51.5, 51.5, 51.5, 51.1, 50.1, 50, 50.1, 50, 49.6, 49.5, 49.5, 49.5, 49.1, 48.6,
                                 48.1, 47.2, 46.1, 45, 43.8, 42.6, 41.5, 40.3, 38.5, 37, 35.2, 33.8, 32.5, 31.5, 30.6,
                                 30.5, 30, 29, 27.5, 24.8, 21.5, 20.1, 19.1, 18.5, 17, 15.5, 12.5, 10.8, 8, 4.7, 1.4, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 4.3, 7.6, 10.9, 14.2, 17.3, 20, 22.5, 23.7,
                                 25.2, 26.6, 28.1, 30, 30.8, 31.6, 32.1, 32.8, 33.6, 34.5, 34.6, 34.9, 34.8, 34.5, 34.7,
                                 35.5, 36, 36, 36, 36, 36, 36, 36.1, 36.4, 36.5, 36.4, 36, 35.1, 34.1, 33.5, 31.4, 29,
                                 25.7, 23, 20.3, 17.5, 14.5, 12, 8.7, 5.4, 2.1, 0, 0, 0, 0, 0, 0, 2.6, 5.9, 9.2, 12.5,
                                 15.8, 19.1, 22.4, 25, 25.6, 27.5, 29, 30, 30.1, 30, 29.7, 29.3, 28.8, 28, 25, 21.7,
                                 18.4, 15.1, 11.8, 8.5, 5.2, 1.9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 3.3, 6.6, 9.9, 13.2, 16.5, 19.8, 23.1, 26.4, 27.8, 29.1, 31.5, 33, 33.6, 34.8, 35.1,
                                 35.6, 36.1, 36, 36.1, 36.2, 36, 35.7, 36, 36, 35.6, 35.5, 35.4, 35.2, 35.2, 35.2, 35.2,
                                 35.2, 35.2, 35, 35.1, 35.2, 35.5, 35.2, 35, 35, 35, 34.8, 34.6, 34.5, 33.5, 32, 30.1,
                                 28, 25.5, 22.5, 19.8, 16.5, 13.2, 10.3, 7.2, 4, 1, 0))

ftp_phase2_time = np.array((
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
    49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
    72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94,
    95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131,
    132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149,
    150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167,
    168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185,
    186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203,
    204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221,
    222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239,
    240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257,
    258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275,
    276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293,
    294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311,
    312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
    330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347,
    348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365,
    366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383,
    384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401,
    402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419,
    420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437,
    438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455,
    456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473,
    474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491,
    492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509,
    510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527,
    528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545,
    546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563,
    564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581,
    582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599,
    600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617,
    618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635,
    636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653,
    654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671,
    672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689,
    690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707,
    708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725,
    726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743,
    744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761,
    762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779,
    780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797,
    798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815,
    816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832, 833,
    834, 835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851,
    852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864))

ftp_phase2_speed_mph = np.array((0, 0, 0, 0, 0, 0, 1.2, 3.5, 5.5, 6.5, 8.5, 9.6, 10.5, 11.9, 14, 16, 17.7, 19, 20.1, 21,
                                 22, 23, 23.8, 24.5, 24.9, 25, 25, 25, 25, 25, 25, 25.6, 25.8, 26, 25.6, 25.2, 25, 25,
                                 25, 24.4, 23.1, 19.8, 16.5, 13.2, 9.9, 6.6, 3.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 3.3, 6.6, 9.9, 13, 14.6, 16, 17, 17, 17, 17.5, 17.7, 17.7, 17.5, 17, 16.9,
                                 16.6, 17, 17.1, 17, 16.6, 16.5, 16.5, 16.6, 17, 17.6, 18.5, 19.2, 20.2, 21, 21.1, 21.2,
                                 21.6, 22, 22.4, 22.5, 22.5, 22.5, 22.7, 23.7, 25.1, 26, 26.5, 27, 26.1, 22.8, 19.5,
                                 16.2, 12.9, 9.6, 6.3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 2, 4.5, 7.8, 10.2, 12.5, 14, 15.3, 17.5, 19.6, 21, 22.2, 23.3, 24.5,
                                 25.3, 25.6, 26, 26.1, 26.2, 26.2, 26.4, 26.5, 26.5, 26, 25.5, 23.6, 21.4, 18.5, 16.4,
                                 14.5, 11.6, 8.7, 5.8, 3.5, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.4, 3.3, 4.4,
                                 6.5, 9.2, 11.3, 13.5, 14.6, 16.4, 16.7, 16.5, 16.5, 18.2, 19.2, 20.1, 21.5, 22.5, 22.5,
                                 22.1, 22.7, 23.3, 23.5, 22.5, 21.6, 20.5, 18, 15, 12, 9, 6.2, 4.5, 3, 2.1, 0.5, 0.5,
                                 3.2, 6.5, 9.6, 12.5, 14, 16, 18, 19.6, 21.5, 23.1, 24.5, 25.5, 26.5, 27.1, 27.6, 27.9,
                                 28.3, 28.6, 28.6, 28.3, 28.2, 28, 27.5, 26.8, 25.5, 23.5, 21.5, 19, 16.5, 14.9, 12.5,
                                 9.4, 6.2, 3, 1.5, 1.5, 0.5, 0, 3, 6.3, 9.6, 12.9, 15.8, 17.5, 18.4, 19.5, 20.7, 22,
                                 23.2, 25, 26.5, 27.5, 28, 28.3, 28.9, 28.9, 28.9, 28.8, 28.5, 28.3, 28.3, 28.3, 28.2,
                                 27.6, 27.5, 27.5, 27.5, 27.5, 27.5, 27.5, 27.6, 28, 28.5, 30, 31, 32, 33, 33, 33.6, 34,
                                 34.3, 34.2, 34, 34, 33.9, 33.6, 33.1, 33, 32.5, 32, 31.9, 31.6, 31.5, 30.6, 30, 29.9,
                                 29.9, 29.9, 29.9, 29.6, 29.5, 29.5, 29.3, 28.9, 28.2, 27.7, 27, 25.5, 23.7, 22, 20.5,
                                 19.2, 19.2, 20.1, 20.9, 21.4, 22, 22.6, 23.2, 24, 25, 26, 26.6, 26.6, 26.8, 27, 27.2,
                                 27.8, 28.1, 28.8, 28.9, 29, 29.1, 29, 28.1, 27.5, 27, 25.8, 25, 24.5, 24.8, 25.1, 25.5,
                                 25.7, 26.2, 26.9, 27.5, 27.8, 28.4, 29, 29.2, 29.1, 29, 28.9, 28.5, 28.1, 28, 28, 27.6,
                                 27.2, 26.6, 27, 27.5, 27.8, 28, 27.8, 28, 28, 28, 27.7, 27.4, 26.9, 26.6, 26.5, 26.5,
                                 26.5, 26.3, 26.2, 26.2, 25.9, 25.6, 25.6, 25.9, 25.8, 25.5, 24.6, 23.5, 22.2, 21.6,
                                 21.6, 21.7, 22.6, 23.4, 24, 24.2, 24.4, 24.9, 25.1, 25.2, 25.3, 25.5, 25.2, 25, 25, 25,
                                 24.7, 24.5, 24.3, 24.3, 24.5, 25, 25, 24.6, 24.6, 24.1, 24.5, 25.1, 25.6, 25.1, 24, 22,
                                 20.1, 16.9, 13.6, 10.3, 7, 3.7, 0.4, 0, 0, 0, 2, 5.3, 8.6, 11.9, 15.2, 17.5, 18.6, 20,
                                 21.1, 22, 23, 24.5, 26.3, 27.5, 28.1, 28.4, 28.5, 28.5, 28.5, 27.7, 27.5, 27.2, 26.8,
                                 26.5, 26, 25.7, 25.2, 24, 22, 21.5, 21.5, 21.8, 22.5, 23, 22.8, 22.8, 23, 22.7, 22.7,
                                 22.7, 23.5, 24, 24.6, 24.8, 25.1, 25.5, 25.6, 25.5, 25, 24.1, 23.7, 23.2, 22.9, 22.5,
                                 22, 21.6, 20.5, 17.5, 14.2, 10.9, 7.6, 4.3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.2, 4, 7.3, 10.6, 13.9, 17, 18.5,
                                 20, 21.8, 23, 24, 24.8, 25.6, 26.5, 26.8, 27.4, 27.9, 28.3, 28, 27.5, 27, 27, 26.3,
                                 24.5, 22.5, 21.5, 20.6, 18, 15, 12.3, 11.1, 10.6, 10, 9.5, 9.1, 8.7, 8.6, 8.8, 9, 8.7,
                                 8.6, 8, 7, 5, 4.2, 2.6, 1, 0, 0.1, 0.6, 1.6, 3.6, 6.9, 10, 12.8, 14, 14.5, 16, 18.1,
                                 20, 21, 21.2, 21.3, 21.4, 21.7, 22.5, 23, 23.8, 24.5, 25, 24.9, 24.8, 25, 25.4, 25.8,
                                 26, 26.4, 26.6, 26.9, 27, 27, 27, 26.9, 26.8, 26.8, 26.5, 26.4, 26, 25.5, 24.6, 23.5,
                                 21.5, 20, 17.5, 16, 14, 10.7, 7.4, 4.1, 0.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 2.1, 5.4, 8.7, 12, 15.3, 18.6, 21.1, 23, 23.5, 23, 22.5, 20, 16.7, 13.4, 10.1,
                                 6.8, 3.5, 0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.2, 1.5, 3.5, 6.5, 9.8, 12, 12.9, 13,
                                 12.6, 12.8, 13.1, 13.1, 14, 15.5, 17, 18.6, 19.7, 21, 21.5, 21.8, 21.8, 21.5, 21.2,
                                 21.5, 21.8, 22, 21.9, 21.7, 21.5, 21.5, 21.4, 20.1, 19.5, 19.2, 19.6, 19.8, 20, 19.5,
                                 17.5, 15.5, 13, 10, 8, 6, 4, 2.5, 0.7, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1.6, 3,
                                 4, 5, 6.3, 8, 10, 10.5, 9.5, 8.5, 7.6, 8.8, 11, 14, 17, 19.5, 21, 21.8, 22.2, 23, 23.6,
                                 24.1, 24.5, 24.5, 24, 23.5, 23.5, 23.5, 23.5, 23.5, 23.5, 24, 24.1, 24.5, 24.7, 25,
                                 25.4, 25.6, 25.7, 26, 26.2, 27, 27.8, 28.3, 29, 29.1, 29, 28, 24.7, 21.4, 18.1, 14.8,
                                 11.5, 8.2, 4.9, 1.6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 1.5, 4.8, 8.1, 11.4, 13.2, 15.1, 16.8, 18.3, 19.5, 20.3, 21.3, 21.9, 22.1,
                                 22.4, 22, 21.6, 21.1, 20.5, 20, 19.6, 18.5, 17.5, 16.5, 15.5, 14, 11, 8, 5.2, 2.5, 0,
                                 0, 0))

hwfet_time = np.array((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                       27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
                       51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
                       75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
                       99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
                       118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136,
                       137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
                       156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174,
                       175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193,
                       194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
                       213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231,
                       232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250,
                       251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269,
                       270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288,
                       289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307,
                       308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326,
                       327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345,
                       346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364,
                       365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383,
                       384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402,
                       403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421,
                       422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440,
                       441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459,
                       460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478,
                       479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497,
                       498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516,
                       517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535,
                       536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554,
                       555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573,
                       574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592,
                       593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611,
                       612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630,
                       631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649,
                       650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668,
                       669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687,
                       688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706,
                       707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725,
                       726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744,
                       745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763,
                       765))

hwfet_speed_mph = np.array((0, 0, 0, 2, 4.9, 8.1, 11.3, 14.5, 17.3, 19.6, 21.8, 24, 25.8, 27.1, 28, 29, 30, 30.7, 31.5,
                            32.2, 32.9, 33.5, 34.1, 34.6, 34.9, 35.1, 35.7, 35.9, 35.8, 35.3, 34.9, 34.5, 34.6, 34.8,
                            35.1, 35.7, 36.1, 36.2, 36.5, 36.7, 36.9, 37, 37, 37, 37, 37, 37, 37.1, 37.3, 37.8, 38.6,
                            39.3, 40, 40.7, 41.4, 42.2, 42.9, 43.5, 44, 44.3, 44.5, 44.8, 44.9, 45, 45.1, 45.4, 45.7,
                            46, 46.3, 46.5, 46.8, 46.9, 47, 47.1, 47.2, 47.3, 47.2, 47.1, 47, 46.9, 46.9, 46.9, 47,
                            47.1, 47.1, 47.2, 47.1, 47, 46.9, 46.5, 46.3, 46.2, 46.3, 46.5, 46.9, 47.1, 47.4, 47.7, 48,
                            48.2, 48.5, 48.8, 49.1, 49.2, 49.1, 49.1, 49, 49, 49.1, 49.2, 49.3, 49.4, 49.5, 49.5, 49.5,
                            49.4, 49.1, 48.9, 48.6, 48.4, 48.1, 47.7, 47.4, 47.3, 47.5, 47.8, 47.9, 48, 47.9, 47.9,
                            47.9, 48, 48, 48, 47.9, 47.3, 46, 43.3, 41.2, 39.5, 39.2, 39, 39, 39.1, 39.5, 40.1, 41, 42,
                            43.1, 43.7, 44.1, 44.3, 44.4, 44.6, 44.7, 44.9, 45.2, 45.7, 45.9, 46.3, 46.8, 46.9, 47,
                            47.1, 47.6, 47.9, 48, 48, 47.9, 47.8, 47.3, 46.7, 46.2, 45.9, 45.7, 45.5, 45.4, 45.3, 45,
                            44, 43.1, 42.2, 41.5, 41.5, 42.1, 42.9, 43.5, 43.9, 43.6, 43.3, 43, 43.1, 43.4, 43.9, 44.3,
                            44.6, 44.9, 44.8, 44.4, 43.9, 43.4, 43.2, 43.2, 43.1, 43, 43, 43.1, 43.4, 43.9, 44, 43.5,
                            42.6, 41.5, 40.7, 40, 40, 40.3, 41, 42, 42.7, 43.1, 43.2, 43.4, 43.9, 44.3, 44.7, 45.1,
                            45.4, 45.8, 46.5, 46.9, 47.2, 47.4, 47.3, 47.3, 47.2, 47.2, 47.2, 47.1, 47, 47, 46.9, 46.8,
                            46.9, 47, 47.2, 47.5, 47.9, 48, 48, 48, 48, 48, 48.1, 48.2, 48.2, 48.1, 48.6, 48.9, 49.1,
                            49.1, 49.1, 49.1, 49.1, 49, 48.9, 48.2, 47.7, 47.5, 47.2, 46.7, 46.2, 46, 45.8, 45.6, 45.4,
                            45.2, 45, 44.7, 44.5, 44.2, 43.5, 42.8, 42, 40.1, 38.6, 37.5, 35.8, 34.7, 34, 33.3, 32.5,
                            31.7, 30.6, 29.6, 28.8, 28.4, 28.6, 29.5, 31.4, 33.4, 35.6, 37.5, 39.1, 40.2, 41.1, 41.8,
                            42.4, 42.8, 43.3, 43.8, 44.3, 44.7, 45, 45.2, 45.4, 45.5, 45.8, 46, 46.1, 46.5, 46.8, 47.1,
                            47.7, 48.3, 49, 49.7, 50.3, 51, 51.7, 52.4, 53.1, 53.8, 54.5, 55.2, 55.8, 56.4, 56.9, 57,
                            57.1, 57.3, 57.6, 57.8, 58, 58.1, 58.4, 58.7, 58.8, 58.9, 59, 59, 58.9, 58.8, 58.6, 58.4,
                            58.2, 58.1, 58, 57.9, 57.6, 57.4, 57.2, 57.1, 57, 57, 56.9, 56.9, 56.9, 57, 57, 57, 57, 57,
                            57, 57, 57, 57, 56.9, 56.8, 56.5, 56.2, 56, 56, 56, 56.1, 56.4, 56.7, 56.9, 57.1, 57.3,
                            57.4, 57.4, 57.2, 57, 56.9, 56.6, 56.3, 56.1, 56.4, 56.7, 57.1, 57.5, 57.8, 58, 58, 58, 58,
                            58, 58, 57.9, 57.8, 57.7, 57.7, 57.8, 57.9, 58, 58.1, 58.4, 58.9, 59.1, 59.4, 59.8, 59.9,
                            59.9, 59.8, 59.6, 59.4, 59.2, 59.1, 59, 58.9, 58.7, 58.6, 58.5, 58.4, 58.4, 58.3, 58.2,
                            58.1, 58, 57.9, 57.9, 57.9, 57.9, 57.9, 58, 58.1, 58.1, 58.2, 58.2, 58.2, 58.1, 58, 58, 58,
                            58, 58, 58, 57.9, 57.9, 58, 58.1, 58.1, 58.2, 58.3, 58.3, 58.3, 58.2, 58.1, 58, 57.8, 57.5,
                            57.1, 57, 56.6, 56.1, 56, 55.8, 55.5, 55.2, 55.1, 55, 54.9, 54.9, 54.9, 54.9, 54.9, 54.9,
                            55, 55, 55, 55, 55, 55, 55.1, 55.1, 55, 54.9, 54.9, 54.8, 54.7, 54.6, 54.4, 54.3, 54.3,
                            54.2, 54.1, 54.1, 54.1, 54, 54, 54, 54, 54, 54, 54, 54, 54.1, 54.2, 54.5, 54.8, 54.9, 55,
                            55.1, 55.2, 55.2, 55.3, 55.4, 55.5, 55.6, 55.7, 55.8, 55.9, 56, 56, 56, 56, 56, 56, 56, 56,
                            56, 56, 56, 56, 56, 56, 55.9, 55.9, 55.9, 55.8, 55.6, 55.4, 55.2, 55.1, 55, 54.9, 54.6,
                            54.4, 54.2, 54.1, 53.8, 53.4, 53.3, 53.1, 52.9, 52.6, 52.4, 52.2, 52.1, 52, 52, 52, 52,
                            52.1, 52, 52, 51.9, 51.6, 51.4, 51.4, 50.7, 50.3, 49.8, 49.3, 48.7, 48.2, 48.1, 48, 48,
                            48.1, 48.4, 48.9, 49, 49.1, 49.1, 49, 49, 48.9, 48.6, 48.3, 48, 47.9, 47.8, 47.7, 47.9,
                            48.3, 49, 49.1, 49, 48.9, 48, 47.1, 46.2, 46.1, 46.1, 46.2, 46.9, 47.8, 49, 49.7, 50.6,
                            51.5, 52.2, 52.7, 53, 53.6, 54, 54.1, 54.4, 54.7, 55.1, 55.4, 55.4, 55, 54.5, 53.6, 52.5,
                            50.2, 48.2, 46.5, 46.2, 46, 46, 46.3, 46.8, 47.5, 48.2, 48.8, 49.5, 50.2, 50.7, 51.1, 51.7,
                            52.2, 52.5, 52.1, 51.6, 51.1, 51, 51, 51.1, 51.4, 51.7, 52, 52.2, 52.5, 52.8, 52.7, 52.6,
                            52.3, 52.3, 52.4, 52.5, 52.7, 52.7, 52.4, 52.1, 51.7, 51.1, 50.5, 50.1, 49.8, 49.7, 49.6,
                            49.5, 49.5, 49.7, 50, 50.2, 50.6, 51.1, 51.6, 51.9, 52, 52.1, 52.4, 52.9, 53.3, 53.7, 54.2,
                            54.5, 54.8, 55, 55.5, 55.9, 56.1, 56.3, 56.4, 56.5, 56.7, 56.9, 57, 57.3, 57.7, 58.2, 58.8,
                            59.1, 59.2, 59.1, 58.8, 58.5, 58.1, 57.7, 57.3, 57.1, 56.8, 56.5, 56.2, 55.5, 54.6, 54.1,
                            53.7, 53.2, 52.9, 52.5, 52, 51.3, 50.5, 49.5, 48.5, 47.6, 46.8, 45.6, 44.2, 42.5, 39.2,
                            35.9, 32.6, 29.3, 26.8, 24.5, 21.5, 19.5, 17.4, 15.1, 12.4, 9.7, 7, 5, 3.3, 2, 0.7, 0, 0))


class DriveQualityStats:
    def __init__(self):
        self.time_secs = 0
        self.CEt_J = 0
        self.CEt_Jpm = 0
        self.Dt_m = 0
        self.IWt_J = 0
        self.IWt_Jpm = 0
        self.CErlt_J = 0
        self.CErlt_Jpm = 0
        self.EngCErlt_J = 0
        self.EngCErlt_Jpm = 0

    def __repr__(self):
        s = '\nSAE J2951 Drive Quality Metrics:\n'
        s = s + 'Time secs      %f\n' %  self.time_secs
        s = s + 'Dt mi          %f\n' % (self.Dt_m / 1609.344)
        s = s + 'Dt m           %f\n' % self.Dt_m
        s = s + 'CEt MJ         %f\n' % (self.CEt_J / 10 ** 6)
        s = s + 'CEt J/m        %f\n' % self.CEt_Jpm
        s = s + 'IWt MJ         %f\n' % (self.IWt_J / 10 ** 6)
        s = s + 'IWt dist J/m   %f\n' % self.IWt_Jpm
        s = s + 'CErlt MJ       %f\n' % (self.CErlt_J / 10 ** 6)
        s = s + 'CErlt J/m      %f\n' % self.CErlt_Jpm
        s = s + 'EngCErlt MJ    %f\n' % (self.EngCErlt_J / 10 ** 6)
        s = s + 'EngCErlt J/m   %f\n' % self.EngCErlt_Jpm
        return s


def CFR_FTP_harmonic_average(bag123_distances, bag123_quantities):
    # FTP_harmonic_average calculates a weighted FTP result from
    # bag1..3 quantities (gallons / grams / energy) and distances
    # weighted 43% "cold" (bags 1&2) and 57% "hot" (bags 3&2)
    # as per CFR 86.144-94

    quant_per = 0.43 * ( (bag123_quantities[0] + bag123_quantities[1] ) / ( bag123_distances[0] + bag123_distances[1]) ) + \
                     0.57 * ( (bag123_quantities[2] + bag123_quantities[1] ) / ( bag123_distances[2] + bag123_distances[1]) )

    # dist_per_quant = 1 / quant_per

    return quant_per # , dist_per_quant


def CFR_city_highway_weighted_combined(city, highway, mode='quant_per_dist'):
    # city_highway_weighted_combined calculates a weighted combined result from
    # city/highway quantities (gallons / grams / energy) per (mi / m / km) or
    # (mi / m /km) per quantity (gallons / grams / energy), depending on the
    # varargs, weighted 55% "city" and 45% "highway"

    if mode is 'dist_per_quant' or mode is 'mpg':
        answer = 1 / (0.55 / city + 0.45 / highway)
    else:
        answer = (0.55 * city + 0.45 * highway)

    return answer

def SAEJ2951_target_inertia_and_roadload_calcs(A_LBSF, B_LBSF, C_LBSF, ETW_LBS, MPH, TIME, do_plots=False,
                                               verbose=False):
    if do_plots:
        plt.plot(ftp_phase1_time, ftp_phase1_speed_mph)
        plt.plot(ftp_phase2_time, ftp_phase2_speed_mph)
        plt.plot(hwfet_time, hwfet_speed_mph)
        plt.grid()
        plt.show()

    drive_quality_stats = DriveQualityStats()

    F0_N = A_LBSF * convert.lbf2N
    Fl_Npms = B_LBSF * convert.lbf2N / convert.mph2mps
    F2_Npms2 = C_LBSF * convert.lbf2N / convert.mph2mps ** 2

    ETW_kg = ETW_LBS * convert.lbm2kg

    Me_kg = 1.015 * ETW_kg

    phase_time = TIME
    phase_time = phase_time - phase_time[0]

    time = np.interp(np.arange(0, phase_time[-1]+0.1, 0.1), phase_time, phase_time)
    Vsched_mps = np.interp(time, phase_time, MPH*convert.mph2mps)

    # VEHICLE SPEED FILTER, FIRST PASS
    Vt_tmp_mps = np.zeros(len(time))

    for i in range(2, len(time) - 2):
        Vt_tmp_mps[i] = 1 / 5 * (Vsched_mps[i - 2] + Vsched_mps[i - 1] + Vsched_mps[i] + Vsched_mps[i + 1] + Vsched_mps[i + 2])

    Vt_mps = Vt_tmp_mps

    Vt_tmp_mps = np.zeros(len(time))
    # VEHICLE SPEED FILTER, SECOND PASS
    for i in range(2, len(time) - 2):
        Vt_tmp_mps[i] = 1 / 5 * (Vt_mps[i - 2] + Vt_mps[i - 1] + Vt_mps[i] + Vt_mps[i + 1] + Vt_mps[i + 2])

    Vt_mps = Vt_tmp_mps

    if do_plots:
        plt.figure()
        plt.plot(TIME, MPH*convert.mph2mps,'o')
        plt.plot(time, Vsched_mps,'.')
        plt.plot(time, Vt_mps, 'r-')
        plt.grid()
        plt.show()

    # ROAD LOAD FORCES(Newtons)
    Frlt_N = np.zeros(len(time))
    for i in range(0, len(Frlt_N)):
        Frlt_N[i] = F0_N + Fl_Npms * Vt_mps[i] + F2_Npms2 * Vt_mps[i]**2  # Newtons

    if do_plots:
        plt.figure()
        plt.plot(time, Frlt_N)
        plt.grid()
        plt.show()

    # ACCELERATION CALCS (m / s^2)
    at_mps2 = np.zeros(len(time))
    for i in range(1,len(time) - 1):
        at_mps2[i] = (Vt_mps[i + 1] - Vt_mps[i - 1]) / 0.2  # Sample period is 0.1 seconds.

    if do_plots:
        plt.figure()
        plt.plot(time, at_mps2)
        plt.grid()
        plt.show()

    # DISTANCE CALCULATIONS (meters)
    dt_m = np.zeros(len(time))

    for i in range(1, len(time)):
        dt_m[i] = Vt_mps[i] * 0.1  # m. Sample period is 0.1 seconds.

    drive_quality_stats.Dt_m = sum(dt_m)
    
    # INERTIA FORCES (Newtons)
    Fit_N = np.zeros(len(time))

    for i in range(0, len(time)):
        Fit_N[i] = Me_kg * at_mps2[i]

    # INERTIAL WORK (Joules)
    IWt_J = 0
    for i in range(0, len(time)):
        if Fit_N[i] >= 0:
            IWt_J = IWt_J + Fit_N[i] * dt_m[i]

    # INERTIAL WORK RATING
    # Inertial work (J and J / m)
    drive_quality_stats.IWt_J = IWt_J
    drive_quality_stats.IWt_Jpm = IWt_J / drive_quality_stats.Dt_m

    # "ENGINE" FORCE (Newtons)
    Fengt_N = np.zeros(len(time))

    for i in range(0, len(time)):
        if Frlt_N[i] + Fit_N[i] >= 0:
            Fengt_N[i] = (Frlt_N[i] + Fit_N[i])
        else:
            Fengt_N[i] = 0

    # ENGINE WORK (Joules)
    Wengt_J = np.zeros(len(time))

    for i in range(0, len(time)):
        Wengt_J[i] = Fengt_N[i] * dt_m[i]

    # roadload required energy (Joules)
    Wrlt_J = np.zeros(len(time))

    for i in range(0, len(time)):
        Wrlt_J[i] = Frlt_N[i] * dt_m[i]

    # CYCLE ENERGY (Joules)
    drive_quality_stats.CEt_J = sum(Wengt_J)

    # total roadload cycle energy(Joules)
    drive_quality_stats.CErlt_J = sum(Wrlt_J)

    # roadload work required from engine

    drive_quality_stats.EngCErlt_J = drive_quality_stats.CEt_J - drive_quality_stats.IWt_J

    # CYCLE ENERGY INTENSITY (J / m)
    drive_quality_stats.CEt_Jpm = drive_quality_stats.CEt_J / drive_quality_stats.Dt_m
    drive_quality_stats.CErlt_Jpm = drive_quality_stats.CErlt_J / drive_quality_stats.Dt_m

    # required roadload demand
    drive_quality_stats.EngCErlt_Jpm = drive_quality_stats.EngCErlt_J / drive_quality_stats.Dt_m

    # ABSOLUTE POWER CHANGE PER TIME
    drive_quality_stats.time_secs = len(time) * 0.1  # Sample period is 0.1 seconds.

    return drive_quality_stats


if __name__ == "__main__":
    A = 49.0198
    B = -0.34687
    C = 0.021146
    ETW = 3625

    dqs_ftp1 = SAEJ2951_target_inertia_and_roadload_calcs(A, B, C, ETW, ftp_phase1_speed_mph, ftp_phase1_time, do_plots=False)
    dqs_ftp2 = SAEJ2951_target_inertia_and_roadload_calcs(A, B, C, ETW, ftp_phase2_speed_mph, ftp_phase2_time, do_plots=False)
    dqs_hwfet = SAEJ2951_target_inertia_and_roadload_calcs(A, B, C, ETW, hwfet_speed_mph, hwfet_time, do_plots=False)

    ftp_IWt_Jpm = CFR_FTP_harmonic_average((dqs_ftp1.Dt_m, dqs_ftp2.Dt_m, dqs_ftp1.Dt_m), (dqs_ftp1.IWt_J, dqs_ftp2.IWt_J, dqs_ftp1.IWt_J))
    ftp_EngCErlt_Jpm = CFR_FTP_harmonic_average((dqs_ftp1.Dt_m, dqs_ftp2.Dt_m, dqs_ftp1.Dt_m), (dqs_ftp1.EngCErlt_J, dqs_ftp2.EngCErlt_J, dqs_ftp1.EngCErlt_J))
    ftp_EngCE_Jpm = CFR_FTP_harmonic_average((dqs_ftp1.Dt_m, dqs_ftp2.Dt_m, dqs_ftp1.Dt_m), (dqs_ftp1.CEt_J, dqs_ftp2.CEt_J, dqs_ftp1.CEt_J))

    weighted_combined_IWt_Jpm = CFR_city_highway_weighted_combined(ftp_IWt_Jpm, dqs_hwfet.IWt_Jpm, mode='quant_per')
    weighted_combined_EngCErlt_Jpm = CFR_city_highway_weighted_combined(ftp_EngCErlt_Jpm, dqs_hwfet.EngCErlt_Jpm, mode='quant_per')
    weighted_combined_EngCE_Jpm = CFR_city_highway_weighted_combined(ftp_EngCE_Jpm, dqs_hwfet.CEt_Jpm, mode='quant_per')
