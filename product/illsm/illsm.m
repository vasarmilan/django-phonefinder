A  = [ ...
1	    5	    3	    7	    6	    6	    1/3	    1/4     ;  ...
1/5	    1	    0	    5	    0	    3	    0	    1/7     ;  ...
1/3         0	    1	    0	    3	    0	    6	    0       ;  ...
1/7	    1/5	    0	    1	    0	    1/4	    0	    1/8     ;  ...
1/6	    0	    1/3	    0	    1	    0	    1/5	    0       ;  ...
1/6	    1/3	    0	    4	    0	    1	    0	    1/6     ;  ...
3	    0	    1/6     0	    5	    0	    1	    0       ;  ...
4	    7	    0	    8	    0	    6	    0	    1      ];


M = A;
matrixsize = max(size(M));

L = zeros(matrixsize-1,matrixsize-1);


for indexi = 1:matrixsize-1
    Degree = matrixsize-1;
    for indexj = 1:matrixsize
        if M(indexi,indexj) == 0
            Degree = Degree - 1;
        end;
    end;  
    L(indexi,indexi) = Degree;
end;

for indexi = 1:matrixsize-2
    for indexj = indexi+1:matrixsize-1
        if M(indexi,indexj) == 0
        else
            L(indexi,indexj) = -1;
            L(indexj,indexi) = -1; 
        end;
    end;
end;


if det(L) == 0 
    ## disp('The graph of the incomplete pairwise comparison matrix you entered is not yet connected. Please provide additional elements.')
else    
    RHS = zeros(matrixsize-1,1);
    for indexj = 1:matrixsize-1
       ColumnProduct = 1;
       for indexi = 1:matrixsize
           if M(indexi,indexj) == 0 
              M(indexi,indexj) = 1; 
           end;   
           ColumnProduct = ColumnProduct * (M(indexi,indexj));
           ## disp(ColumnProduct)
           ## disp("\n\n\n")
       end;       
       RHS(indexj,1) = -log(ColumnProduct) ;
    end;        
    y = inv(L)*RHS;  
    disp(y)
    w = (exp(y))';
    w(matrixsize) = 1;
    ## disp(w)
    w = w/sum(w);
    ## disp('incomplete LLSM weights normalized by sum w_i = 1');
    ## disp("\n\n")
    ## disp(w);
end;
