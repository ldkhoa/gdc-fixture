Check output validity:
  $ $TESTDIR/generate_csv -s 1 -i 4 -p 3 2016 2016
  "tab_inv_item.col_quantity","tab_inv_item.col_total","tab_inv.col_total","tab_inv.col_name","tab_inv.dt_invoice","tab_pers.col_bn","tab_pers.col_fn","tab_pers.col_sn","tab_pers.col_hn"
  7,24,5,inv-0000000000000000000000000001,2016-01-12,2,"Ina","Millican","Ina Millican"
  5,23,1,inv-0000000000000000000000000002,2016-06-13,2,"Ina","Millican","Ina Millican"
  3,29,46,inv-0000000000000000000000000003,2016-01-12,0,"Burrell","Kellam","Burrell Kellam"
  6,29,20,inv-0000000000000000000000000004,2016-03-21,1,"Rockley","Reiff","Rockley Reiff"
